import os
import time
import samweb_client
import argparse
import threading


'''
    Useful testing definitions
    #definition = 'bjwhite_ifdh_test' # SAMDEV
    #definition = 'bjwhite_mid_test' # SAMDEV
    #definition = 'bjwhite_scale_test' # SAMDEV (ALL FILES) 
    #definition = 'bjwhite_enstore_dataset_1' # SAMDEV
    #definition = 'poms_depends_466544_1' # GM2
'''

def parse_args(parser):
    parser.add_argument('--experiment', default='sam_bjwhite', help='SAM Experiment. Default: sam_bjwhite')
    parser.add_argument('--defname', default='bjwhite_ifdh_test', help='SAM Definition to run a project on. Default: bjwhite_ifdh_test')
    parser.add_argument('--station', default='bjwhite_python_station', help='SAM Station to run the project on. Default: bjwhite_python_station')
    parser.add_argument('--group', default='samdev', help='SAM Group to run the project under. Default: samdev')
    parser.add_argument('--user', default='bjwhite', help='SAM user that the project will be ran as. Default: bjwhite')
    parser.add_argument('--node', default='fermicloud106.fnal.gov', help='Hostname of node SAM files will be delivered to?. Default: fermicloud106.fnal.gov')
    parser.add_argument('--description', default='bjwhite_testing', help='Description to be provided to processes')
    parser.add_argument('--schemas', default='gsiftp', help='Comma separated list of acceptable protocols. (ex. gsiftp, xrootd, ...). Default: xrootd')
    parser.add_argument('--num-threads', type=int, default=1, help='Number of threads to run program with. Use consumers-per-thread to controll number of SAM consumers per running thread.')
    parser.add_argument('--enable-skipped', type=bool, default=False, help='When enabled, a fraction of processed files will be skipped, rather than completed.')
    return parser.parse_args()


def start_project(samweb, project_name, definition, station, user, group):
    print 'Starting Project...'
    project = samweb.startProject(project=project_name, defname=definition, station=station, user=user, group=group)
    time.sleep(1)
    project_url = samweb.findProject(project_name, station) # Normally you can get the project_url from the above project info. Test findProject explicitly
    return project_url


def process_file(samweb, consumer_url, consumer_id, file_info, skip=False):
    filename = file_info['filename']
    print 'Consumer %s processing file %s' % (consumer_id, filename)

    time.sleep(1)
    samweb.setProcessFileStatus(consumer_url, filename, 'transferred')
    print '\t%s: File %s: transferred' % (consumer_id, filename)

    time.sleep(1)
    samweb.setProcessFileStatus(consumer_url, filename, 'consumed')
    print '\t%s: File %s: consumed' % (consumer_id, filename)

    time.sleep(2)
    if skip:
        samweb.setProcessFileStatus(consumer_url, filename, 'skipped')
    else:
        samweb.setProcessFileStatus(consumer_url, filename, 'completed')
    print '\t%s: File %s: completed' % (consumer_id, filename)
    

def run_sam_consumer(samweb, project_url, node, user, description, schemas, enable_skipped):
    print 'Starting consumer process:'
    print '\tNode: ', node
    print '\tUser: ', user 
    print '\tDescription: ', description 
    print '\tSchemas: ', schemas 

    consumer_id = samweb.startProcess(project_url, 'demo', 'demo', 'demo', node=node, user=user, description=description, schemas=schemas)
    consumer_url = samweb.makeProcessUrl(project_url, consumer_id)
    print '\tCreated consumer: %s, %s\n' % (consumer_id, consumer_url)

    count = 0
    while True:
        try:
            file_info = samweb.getNextFile(consumer_url)
        except samweb_client.exceptions.NoMoreFiles as ex:
            break
        if enable_skipped and count % 5 == 0:
            process_file(samweb, consumer_url, consumer_id, file_info, skip=True)
        else:
            process_file(samweb, consumer_url, consumer_id, file_info)
        count += 1
    samweb.setProcessStatus('completed', project_url, consumer_id)
    print 'Process %s: completed' % consumer_id

def main():
    parser = argparse.ArgumentParser()
    args = parse_args(parser) 

    samweb = samweb_client.SAMWebClient(experiment=args.experiment)
    definition = args.defname
    station = args.station
    group = args.group
    user = args.user
    node = args.node
    description = args.description
    schemas = args.schemas
    num_threads = args.num_threads
    enable_skipped = args.enable_skipped

    project_name = time.strftime('bjwhite_ifdh_test_%Y%m%d%H_%%d') % os.getpid()

    print 'Using station: ', station
    print samweb.descDefinition(definition)+'\n'
    
    project_url = start_project(samweb, project_name, definition, station, user, group)
    print 'Project Url: ', project_url 

    if num_threads > 1:
        threads = [] 
        for i in range(0, num_threads):
            threads.append( threading.Thread(target=run_sam_consumer, args=( (samweb, project_url, node, user, description, schemas, enable_skipped) ) ) )
            threads[i].start()
        for i in range(0, num_threads):
            threads[i].join()
    else:
        run_sam_consumer(samweb, project_url, node, user, description, schemas, enable_skipped)

    print 'All processes completed.'
    samweb.stopProject(project_url)
    print 'Ended project: ', project_name


if __name__ == '__main__':
    main()
