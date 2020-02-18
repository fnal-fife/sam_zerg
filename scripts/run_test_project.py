import os
import time
import samweb_client

def main():
    #samweb = samweb_client.SAMWebClient(experiment='samdev')
    samweb = samweb_client.SAMWebClient(experiment='sam_bjwhite')
    #station = 'samdev'
    station = 'bjwhite_python_station'
    group = 'samdev'

    definition = 'bjwhite_ifdh_test'
    #definition = 'bjwhite_enstore_dataset_1'

    proj_name = time.strftime('bjwhite_ifdh_test_%Y%m%d%H_%%d') % os.getpid()

    print 'Using station: ', station
    #print samweb.locateFile('ifdh_test_file_0')
    print samweb.descDefinition(definition)
    
    cpurl = samweb.startProject(project=proj_name, defname=definition, station=station, user='bjwhite', group=group)
    print 'Sleeping 10sec'
    time.sleep(10)
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
            #    samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'transferred')
            #    time.sleep(1)
            #    samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'consumed')
            #    flag = False
            #else:
            #    samweb.setProcessFileStatus(consumer_url, f_info['filename'], 'skipped')
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
