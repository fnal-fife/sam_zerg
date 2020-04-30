import os
import re
import time
import samweb_client
import argparse
import threading
import random


'''
    Useful testing definitions
    #definition = 'bjwhite_parallel_n50'
    #definition = 'bjwhite_ifdh_test' # SAMDEV
    #definition = 'bjwhite_mid_test' # SAMDEV
    #definition = 'bjwhite_scale_test' # SAMDEV (ALL FILES) 
    #definition = 'bjwhite_enstore_dataset_1' # SAMDEV
    #definition = 'poms_depends_466544_1' # GM2
'''

VALID_FORCE_CONSUMER_RESTART_ARGS=['disabled', 'all', 'fraction']
MAX_CONSUMERS = 36
JOB_UNIQUE_ID_BASE_REGEX = re.compile(r"@[a-zA-Z0-9\-.]+$")

def parse_args(parser):
    parser.add_argument('--experiment', default='sam_bjwhite', help='SAM Experiment. Default: sam_bjwhite')
    parser.add_argument('--defname', default='bjwhite_ifdh_test', help='SAM Definition to run a project on. Default: bjwhite_ifdh_test')
    parser.add_argument('--station', default='bjwhite_python_station', help='SAM Station to run the project on. Default: bjwhite_python_station')
    parser.add_argument('--group', default='samdev', help='SAM Group to run the project under. Default: samdev')
    parser.add_argument('--user', default='bjwhite', help='SAM user that the project will be ran as. Default: bjwhite')
    parser.add_argument('--node', default='fermicloud106.fnal.gov', help='Hostname of node SAM files will be delivered to?. Default: fermicloud106.fnal.gov')
    parser.add_argument('--description-base', default='', help='Provide a description suffix to act as the node name. Prefixes will be randomly generated.')
    parser.add_argument('--schemas', default='gsiftp', help='Comma separated list of acceptable protocols. (ex. gsiftp, xrootd, ...). Default: xrootd')
    parser.add_argument('--num-threads', type=int, default=1, help='Number of SAM consumers to be started in parallel threads.')
    parser.add_argument('--enable-skipped', type=bool, default=False, help='When enabled, a fraction of processed files will be skipped, rather than completed.')
    parser.add_argument('--force-consumer-restart', default='disabled', help='Force consumer processes to be restarted, for testing job recovery. Default: disabled\nAcceptable values: all or fraction')
    return parser.parse_args()

def validate_args(args):
    try:
        if args.description_base != '':
            assert JOB_UNIQUE_ID_BASE_REGEX.match(args.description_base) is not None
    except AssertionError as ex:
        raise AssertionError('The provided job unique ID base description (%s) did noth match %s' % 
            (args.description_base, JOB_UNIQUE_ID_BASE_REGEX.pattern)) 
    try:
        assert args.num_threads >= 1 and args.num_threads <= MAX_CONSUMERS
    except AssertionError as ex:
        raise AssertionError('Please use a number of threads in the range [1-%s] - Provided %s' % 
            (MAX_CONSUMERS, args.num_threads) )
    try:
        assert args.force_consumer_restart.lower() in VALID_FORCE_CONSUMER_RESTART_ARGS
    except AssertionError as ex:
        raise AssertionError('The value %s is not a valid identifier in the set %s' % 
            (args.force_consumer_restart, VALID_FORCE_CONSUMER_RESTART_ARGS) )

def start_project(samweb, project_name, definition, station, user, group):
    print('Starting Project...')
    project = samweb.startProject(project=project_name, defname=definition, station=station, user=user, group=group)
    time.sleep(1)
    project_url = samweb.findProject(project_name, station) # Normally you can get the project_url from the above project info. Test findProject explicitly
    return project_url


def process_file(samweb, consumer_url, consumer_id, file_info, skip=False):
    filename = file_info['filename']
    print('Consumer %s processing file %s' % (consumer_id, filename))

    time.sleep(random.randint(1,5))
    try:
        samweb.setProcessFileStatus(consumer_url, filename, 'transferred')
    except samweb_client.exceptions.HTTPBadRequest as ex:
        print('\nERROR:\n\tProcess: %s\n\t' % consumer_id)
        raise
    else:
        print('\t%s: File %s: transferred' % (consumer_id, filename))

    time.sleep(random.randint(1,5))
    try:
        samweb.setProcessFileStatus(consumer_url, filename, 'consumed')
    except samweb_client.exceptions.HTTPBadRequest as ex:
        print('\nERROR:\n\tProcess: %s\n\t' % consumer_id)
        raise
    else:
        print('\t%s: File %s: consumed' % (consumer_id, filename))

    time.sleep(random.randint(1,5))
    if skip:
        try:
            samweb.setProcessFileStatus(consumer_url, filename, 'skipped')
        except samweb_client.exceptions.HTTPBadRequest as ex:
            print('\nERROR:\n\tProcess: %s\n\t' % consumer_id)
            raise
        else:
            print('\t%s: File %s: skipped' % (consumer_id, filename))
    else:
        try:
            samweb.setProcessFileStatus(consumer_url, filename, 'completed')
        except samweb_client.exceptions.HTTPBadRequest as ex:
            print('\nERROR:\n\tProcess: %s\n\t' % consumer_id)
            raise
        else:
            print('\t%s: File %s: completed' % (consumer_id, filename))
    
def do_process_file(samweb, consumer_url, consumer_id, enable_skipped, count):
        try:
            file_info = samweb.getNextFile(consumer_url)
        except samweb_client.exceptions.NoMoreFiles as ex:
            return True
        if enable_skipped and count % 5 == 0: # TODO: Make the skip calculation more robust
            process_file(samweb, consumer_url, consumer_id, file_info, skip=True)
        else:
            process_file(samweb, consumer_url, consumer_id, file_info)

def generate_job_unique_id(description_base):
    if description_base == '':
        return 'test process'
    rand_a = random.randint(0, 99999) 
    rand_b = random.randint(0, 9) 
    prefix = '%s.%s' % (rand_a, rand_b)
    description = prefix + '@' + description_base
    return description

def run_sam_consumer(samweb, project_url, node, user, description_base, schemas, enable_skipped, cancel_target=False):
    print('Starting consumer process:')
    print('\tNode: %s' %  node)
    print('\tUser: %s' % user)
    print('\tDescription Base: %s' % description_base)
    print('\tSchemas: %s' % schemas)

    description = generate_job_unique_id(description_base)
    consumer_id = samweb.startProcess(project_url, 'demo', 'demo', 'demo', node=node, user=user, description=description, schemas=schemas)
    consumer_url = samweb.makeProcessUrl(project_url, consumer_id)
    print('\tCreated consumer: %s, %s, %s' % (consumer_id, consumer_url, description))

    count = 0
    cancelled = False
    stop = False
    while not stop:
        # Check if process needs to be cancelled, is ready to do so, and execute the cancellation if applicable
        if cancel_target:
            print('I (%s) should be doomed eventually... (count: %s)' % (consumer_id, count))
            #defname = consumer_url.split('/')[-3] # N
            # How to find P without passing it in, or having it as a global? Threading library?
            if count > 5: # TODO: Figure out a better heuristic based off of (N/P) * fraction
                samweb.setProcessStatus('cancelled',project_url, consumer_id)
                cancelled = True
                print('Process %s: cancelled after processing %s files' % (consumer_id , count) )
                count = 0
                break
        stop = do_process_file(samweb, consumer_url, consumer_id, enable_skipped, count)
        count += 1

    if cancelled:
        # Restart the processing
        consumer_id = samweb.startProcess(project_url, 'demo', 'demo', 'demo', node=node, user=user, description=description, schemas=schemas)
        consumer_url = samweb.makeProcessUrl(project_url, consumer_id)
        print('\tRestarted consumer: %s, %s\n' % (consumer_id, consumer_url))
        stop = False
        count = 0
        while not stop:
            stop = do_process_file(samweb, consumer_url, consumer_id, enable_skipped, count)
            count += 1

    samweb.setProcessStatus('completed', project_url, consumer_id)
    print('Process %s: completed after processing %s files' % (consumer_id, count) )


def main():
    parser = argparse.ArgumentParser()
    args = parse_args(parser) 
    validate_args(args)

    samweb = samweb_client.SAMWebClient(experiment=args.experiment)
    definition = args.defname
    station = args.station
    group = args.group
    user = args.user
    node = args.node
    description_base = args.description_base
    schemas = args.schemas
    num_threads = args.num_threads
    enable_skipped = args.enable_skipped
    force_cancel = args.force_consumer_restart

    project_name = time.strftime('bjwhite_ifdh_test_%Y%m%d%H_%%d') % os.getpid()

    print('Using station: ', station)
    print(samweb.descDefinition(definition)+'\n')
    
    project_url = start_project(samweb, project_name, definition, station, user, group)
    print('Project Url: ', project_url)

    
    if num_threads > 1:
        threads = [] 
        for i in range(0, num_threads):
            cancel_target = random.choice([True, False]) if force_cancel != 'disabled' else False # Need to improve this beyond totally random cancellations
            threads.append(
                threading.Thread(
                    target=run_sam_consumer, 
                    args=( (samweb, project_url, node, user, description_base, schemas, enable_skipped, cancel_target) ) ) )
            threads[i].start()
        for i in range(0, num_threads):
            threads[i].join()
    else:
        run_sam_consumer(samweb, project_url, node, user, description_base, schemas, enable_skipped)

    print('All processes completed.')
    samweb.stopProject(project_url)
    print('Ended project: ', project_name)


if __name__ == '__main__':
    main()
