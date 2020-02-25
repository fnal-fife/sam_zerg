import os
import time
import samweb_client

def main():
    #samweb = samweb_client.SAMWebClient(experiment='samdev')
    #station = 'samdev'
    #group = 'samdev'

    #samweb = samweb_client.SAMWebClient(experiment='sam_bjwhite')
    #station = 'bjwhite_python_station'
    #group = 'samdev'

    samweb = samweb_client.SAMWebClient(experiment='gm2')
    station = 'gm2'
    group = 'gm2'

    #definition = 'bjwhite_ifdh_test' # SAMDEV
    #definition = 'bjwhite_enstore_dataset_1' # SAMDEV

    definition = 'poms_depends_466544_1' # GM2

    proj_name = time.strftime('bjwhite_ifdh_test_%Y%m%d%H_%%d') % os.getpid()

    print 'Using station: ', station
    print samweb.descDefinition(definition)
    
    cpurl = samweb.startProject(project=proj_name, defname=definition, station=station, user='bjwhite', group=group)
    print 'Sleeping 3 sec'
    time.sleep(3)
    cpurl = samweb.findProject(proj_name, station)
    consumer_id = samweb.startProcess(cpurl, 'demo', 'demo', 'demo', node='fermicloud172.fnal.gov', user='bjwhite')
    print 'got cpurl, consumer_id: ', cpurl, consumer_id
    consumer_url = samweb.makeProcessUrl(cpurl, consumer_id)
    flag = True
    try:
        f_info = samweb.getNextFile(consumer_url)
    except Exception:
        samweb.stopProject(cpurl)
    furi = f_info['filename']
    print 'recieved furi: ', f_info['filename']
    try:
        while furi:
            #if flag:
            #    flag = False
            #    samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'consumed')
            #else:
            #    flag = True
            samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'transferred')
            time.sleep(1)
            samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'consumed')
            time.sleep(1)
            samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'completed')

            f_info = samweb.getNextFile(consumer_url)
            furi = f_info['filename']
            print 'recieved furi: ', f_info['filename']
    except samweb_client.exceptions.NoMoreFiles:
        pass

    samweb.setProcessStatus('completed', cpurl, consumer_id)  

    samweb.stopProject(cpurl)
    

if __name__ == '__main__':
    main()
