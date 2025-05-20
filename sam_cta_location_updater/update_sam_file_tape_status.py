#! /usr/bin/env python3

import argparse
import datetime
import sys
import samweb_client
import psycopg2
import urllib.parse

def main(hostname, port, database, password, experiment, days, dry_run=False):

    if dry_run:
        print('Dry run mode - not performing updates')

    samweb = samweb_client.SAMWebClient(experiment=experiment)

    if days < 0: days = 0
    today = datetime.date.today()
    query_start = today - datetime.timedelta(days=days)

    conn=psycopg2.connect(
            host=hostname,
            port=port,
            dbname=database,
            password=password,
            user='samdbs'
    )


    print(f'Querying since {query_start}')

    cur = conn.cursor(name='tapelocs')

    cur.execute("""select full_path, file_name, file_size_in_bytes, checksum_value 
            from data_file_locations join data_storage_locations using (location_id)
            join data_files using (file_id)
            left join volumes using (volume_id)
            left join (select file_id, checksum_value from checksums
            where checksum_type_id = (select checksum_type_id from checksum_types where checksum_name = 'adler32')) as ck
            on (data_files.file_id = ck.file_id )
            where data_file_locations.create_date > %s
            and location_type='tape' and full_path like '/pnfs/%%'
            and (volume_id is null or volume_id is not null and volume_name = 'unknown')""",
            (query_start,)
            )

    for full_path, file_name, file_size, checksum_value in cur:

        if full_path.startswith('/pnfs/'):
            loc = 'enstore:' + full_path
        else:
            loc = full_path

        adler32 = checksum_value

        if check_dcache_on_tape(samweb, loc, file_name, file_size, adler32):
            print(f"{file_name} is on tape, marking with label")
            params = { "location" : loc, "label": "nearline" }
            if dry_run:
                print(f'Would update {params} for /files/name/{urllib.parse.quote(file_name)}/locations')
            else:
                try:
                    samweb.putURL(f'/files/name/{urllib.parse.quote(file_name)}/locations', params)
                except samweb_client.exceptions.FileNotFound:
                    print(f'File {file_name} is not declared to SAM. Skipping.')

        else:
            print(f"{file_name} is not on tape")

def check_dcache_on_tape(samweb, loc, fname, fsize, adler32):
    if not loc.startswith('enstore:/pnfs/'):
        raise Exception(f'Unexpected file location {loc}')

    subpath = loc[14:]
    path = f'/pnfs/fnal.gov/usr/{subpath}/{fname}'

    try:
        result = samweb.getURL(f'https://fndca.fnal.gov:3880/api/v1/namespace{path}?locality=true&checksum=true&optional=true').json()
    except KeyError: 
        # Use KeyError, since dCache doesn't return something the samweb client likes with for errmsg = err['message'] http_client_urllib.py line 296
        # It's actually a 404, file not found.
        print(f'File {fname} was not found at path {path} in dCache.')
        return False
    locality = result['fileLocality']

    dcache_size = result['size']

    if result['size'] != fsize:
        print(f"{fname} size mismatch")
        return False

    for c in result['checksums']:
        if c["type"].lower() == 'adler32':
            if adler32 and c['value'].lower() != adler32.lower():
                print(f"{fname} checksum mismatch")
                return False

    #print(result)

    if 'NEARLINE' in locality:
        #print(result['suris'])
        if result['suris']:
            return True
        else:
            print(f"{fname} locality is NEARLINE but no suris")
            return False
    else:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--experiment')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-t', '--hostname', help='SAM database hostname')
    parser.add_argument('-p', '--port', help='SAM database port')
    parser.add_argument('-d', '--database', help='SAM database name')
    parser.add_argument('-w', '--password', help='SAM database password')

    args = parser.parse_args()
    main(args.hostname, args.port, args.database, args.password, args.experiment, args.days, args.dry_run)
