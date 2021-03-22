import requests
from zedrunner_store import ZedRunnerStore
import argparse
from mapper import Mapper
from zednotification_bot import Notification

class ZedRun:

    def __init__(self):
        self.mapper = Mapper()
        self.store = ZedRunnerStore()


    def fetch_race_data(self, forced=False):
        url = 'https://zed-ql.zed.run/graphql/'
        cursor = 'null'

        query ="""query{
        get_race_results(first:1000, input: {only_my_racehorses: false}, after: {0}) {
            edges {
            cursor
            node {
            country
            country_code
            city
            name
            length
            start_time
            fee
            race_id
            weather
            status
            class
            prize_pool {
                first
                second
                third
                total 
                }
            horses {
                horse_id 
                finish_time
                final_position
                name
                gate
                owner_address
                bloodline
                gender
                breed_type
                gen
                races
                coat
                win_rate
                career
                hex_color
                img_url
                class
                stable_name 
                } 
            }
            } 

            page_info {
                end_cursor
                has_next_page
            }
         }
            
        } """ 
        while True:
            after_query = query.replace('{0}',cursor)

            response = requests.post(url, json={'query': after_query})
            print(response.status_code)
            jsondata = response.json()
            datas = jsondata['data']['get_race_results']['edges']

            cursor ='"'  + jsondata['data']['get_race_results']['page_info']['end_cursor'] + '"'

            has_next_page = jsondata['data']['get_race_results']['page_info']['has_next_page']

            data_set = self.mapper.map_race_data(datas)
            break_loop = True
            print(cursor)
            if forced or not self.store.race_exists(datas[0]):
                # store races data set
                self.store.store_races(data_set['races'])

                # store races data set
                self.store.store_races_result(data_set['races_results'])
                break_loop = False

            if  break_loop or not has_next_page:
                break
        
    def fetch_horse_data(self, forced=False):
        url = 'https://api.zed.run/api/v1/horses/roster?offset={0}&gen\[\]=1&gen\[\]=268&sort_by=created_by_desc'
        offset = 0
        while True:
            current_url = url.format(offset)
            print("Calling endpoint{}".format(current_url))
            response = requests.get(current_url)
            print(response.status_code)
            jsondata =response.json()
            break_loop = True
            count = len(jsondata)
            offset = offset + count
            first_horse = jsondata[0]
            print(len(jsondata))
            print('Forced' + str(forced))

            if forced or not self.store.horse_exists(first_horse):
                print('Saving horse information')
                horse_datas = self.mapper.map_horses_data(jsondata)
                self.store.store_horses(horse_datas)
                break_loop = False

            if break_loop or count == 0:
                break

    def fetch_stable_data(self,forced=False):
        url = 'https://api.zed.run/api/v1/horses/get_user_horses?public_address={0}&offset={1}&gen\[\]=1&gen\[\]=268&sort_by=created_by_desc&page=2'
        offset = 0
        is_continued = True
        while True:
            current_url = url.format('0x3e238A00438837f48756be5516200dDDFC304865',offset)
            print("Calling endpoint{}".format(current_url))
            response = requests.get(current_url)
            print(response.status_code)
            jsondata =response.json()
            count = len(jsondata)
            offset = offset + count
            first_horse = jsondata[0]
            print('Calling endpoint')

            if not self.store.horse_exists(first_horse):
                horse_datas = self.mapper.map_horses_data(jsondata)
                self.store.store_horses(horse_datas)
                is_continued = False

            if is_continued and count == 10:
                break


def main(type, forced):
    message = f"Zed Run with settings Type:'{type}' and Forced: {forced}"
    try:
        run = ZedRun()
        if(type == 'horse'):
            run.fetch_horse_data(forced)
        elif(type == 'race'):
            run.fetch_race_data(forced)
        elif(type == 'stable'):
            run.fetch_stable_data(forced)

        success_message = message + " completed successfully."

        Notification.send_message(success_message)
    except Exception as e:       
        failure_message = message + ' failed.'
        Notification.send_message(f"Error: {failure_message} Reason {str(e)}")



if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    # Add arguments to parser
    ap.add_argument("-t","--type", required=True, help="type can be horse, race or stable")
    ap.add_argument('-f', '--force', required=False, help="Force and restore cache")
    args = vars(ap.parse_args())
    type = args['type']
    forced = args['force'] or False
    print(type, forced)
    main(type, forced)