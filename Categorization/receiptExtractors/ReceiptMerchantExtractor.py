from Categorization import GoogleOCR
from Categorization import FuncMl
from Categorization.extractors import DateExtractor
from fuzzywuzzy import fuzz
import json
import requests
from commonregex import CommonRegex
from ReceiptAddressExtractorML import ReceiptAddressExtractorML


class ReceiptMerchantExtractor:

    def __init__(self):
        self.google_ocr = GoogleOCR()
        self.class_func = FuncMl()
        self.class_date_extractor = DateExtractor()
        self.class_address_extractor = ReceiptAddressExtractorML()

    @staticmethod
    def __mark_merchant_line(text_lines, line_rect_list):
        """
            Check and mark the Merchant lines
        """
        merchant_rect = None
        name_line_list = []
        page_rect = line_rect_list['rect'][0]
        list_no_name = ['welcome', 'thank you', 'customer', 'copy', 'only', '*', 'ticket',
                        '(', ')', ':', 'invoice', '!', 'more', 'congratulation', 'bill']

        for i in range(len(text_lines)):
            # pre-processing of text line
            for j in range(i + 1, len(line_rect_list['text'])):
                if text_lines[i] == line_rect_list['text'][j]:
                    break

            line_rect = line_rect_list['rect'][j]

            text_lines[i] = text_lines[i].replace('Welcome to', '')
            text_lines[i] = text_lines[i].strip('-')

            # check contains of key in list_no_name
            f_check_no_list = False
            for j in range(len(list_no_name)):
                if text_lines[i].lower().__contains__(list_no_name[j]):
                    f_check_no_list = True
                    break

            if f_check_no_list:
                continue

            # check validation of key
            if len(text_lines[i]) <= 2:
                continue
            elif len(name_line_list) > 0 and name_line_list[-1] + 1 != i:
                break
            elif len(name_line_list) > 0 and text_lines[i].__contains__(text_lines[name_line_list[-1]]):
                continue
            elif len(name_line_list) > 2:
                continue
            elif len(name_line_list) > 1 and not text_lines[i].isupper():
                continue
            elif text_lines[i][0] == '#':
                continue
            elif len(CommonRegex(text_lines[i]).dates) > 0:
                continue
            elif len(CommonRegex(text_lines[i]).phones) > 0:
                continue
            elif len(CommonRegex(text_lines[i]).links) > 0:
                continue
            elif len(text_lines[i].replace('@', '').replace('&', '').split()) > 5:
                continue
            elif len(text_lines[i].split()) > 3 and text_lines[i].__contains__('-'):
                continue
            elif text_lines[i].replace('-', '').replace(' ', '').isdigit():  # '305337 - 1'
                continue
            elif len(name_line_list) > 0 and line_rect[1] > 2 * merchant_rect[3] - merchant_rect[1]:
                continue
            elif (line_rect[0] + line_rect[2]) > (page_rect[0] + page_rect[2]) * 1.3:   # check the position
                continue

            name_line_list.append(i)
            merchant_rect = line_rect

        return name_line_list

    def get_address_string(self, ocr_json):

        # --------------------------- Extract Address -------------------------
        ret_address, first_address_line = self.class_address_extractor.extractor(ocr_json)

        # ------------------------ Remove vertical text -----------------------
        line_data = self.class_func.get_line_rect(ocr_json)
        new_ocr_text = self.class_func.remove_vertical_text(ocr_json)
        text_lines = new_ocr_text.splitlines()

        # --------------------------- Extract Merchant ------------------------
        if first_address_line == -1:
            range_merchant = 5
        else:
            range_merchant = first_address_line

        name_line_list = self.__mark_merchant_line(text_lines[:range_merchant], line_data)

        ret_name = ''
        for i in range(len(name_line_list)):
            ret_name += text_lines[name_line_list[i]] + ' '

        if ret_name.__contains__('#') and len(ret_name.split()) > 2:
            ret_name = ret_name[:ret_name.find('#')]

        ret_name = ret_name.strip('.').strip().replace('  ', ' ').replace('&', '')

        if len(ret_name) > 1 and ret_name[0].islower() and ret_name[1:].isupper():
            ret_name = ret_name.upper()

        return [ret_name, ret_address]

    def get_request_google(self, key_string):
        """
            get the respond from google text search request using key_string.
        """
        if key_string is None:
            return None

        response = requests.post(url='https://maps.googleapis.com/maps/api/place/textsearch/json?key=' +
                                     self.class_func.google_key + '&query=' + key_string,
                                 headers={'Content-Type': 'application/json'})

        return response.text

    def get_request_google_nearby(self, position):
        """
            get the respond from google text search request using key_string.
        """
        url_info = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=' + \
                   str(position[0]) + ',' + str(position[1]) + '&key=' + self.class_func.google_key + \
                   '&radius=500'
        response = requests.post(url=url_info, headers={'Content-Type': 'application/json'})

        return response.text

    def get_request_google_place_detail(self, place_id):
        """
            get the respond from google place details request using key_string.
        """
        url_info = 'https://maps.googleapis.com/maps/api/place/details/json?placeid=' + place_id + \
                   '&key=' + self.class_func.google_key

        response = requests.post(url=url_info, headers={'Content-Type': 'application/json'})

        return response.text

    def extract(self, filename=None, ocr_json=None):
        """
            get some google search data from ocr json data.
        """
        if ocr_json is None:
            ocr_json = self.google_ocr.get_json_google(filename)

        # ------------ Get merchant and address from text, and logo -----------
        ret_logo_key_json = self.google_ocr.get_json_google(filename, detection_type='logo')
        if ret_logo_key_json is not None:
            ret_logo_key = ret_logo_key_json[0]['description']
        else:
            ret_logo_key = ''

        ret_address = self.get_address_string(ocr_json)
        if ret_address is None:
            return ['', '', ret_logo_key, '', '']
        else:
            [ret_name, ret_address] = ret_address

        # --------- extract the merchant info using title and address ---------
        ret_merchant_key = ret_name + ' ' + ret_address
        ret_merchant = self.get_request_google(ret_merchant_key)

        if ret_merchant is not None:
            ret_merchant_json = json.loads(ret_merchant)
            if ret_merchant_json['status'] == 'OK':
                ret_result = ret_merchant_json['results'][0]
                return [ret_result['formatted_address'],
                        ret_result['icon'],
                        ret_result['name'],
                        ret_result['types'],
                        ret_result['place_id']]

        # -------- extract the merchant info using logo + address -------------
        ret_address_info = self.get_request_google(ret_address)

        if ret_address_info is not None:
            ret_address_info_json = json.loads(ret_address_info)
            if ret_address_info_json['status'] == 'OK':
                ret_result = ret_address_info_json['results'][0]
                if len(ret_result['types']) > 1:  # except type=['street']
                    return [ret_result['formatted_address'],
                            ret_result['icon'],
                            ret_result['name'],
                            ret_result['types'],
                            ret_result['place_id']]

        if ret_logo_key != '':
            ret_full_address_info = self.get_request_google(ret_logo_key + ' ' + ret_address)

            if ret_full_address_info is not None:
                ret_address_info_json = json.loads(ret_full_address_info)
                if ret_address_info_json['status'] == 'OK':
                    ret_result = ret_address_info_json['results'][0]
                    return [ret_result['formatted_address'],
                            ret_result['icon'],
                            ret_result['name'],
                            ret_result['types'],
                            ret_result['place_id']]

        # --------- extract the merchant info using only address --------------
        # get position list of address
        if ret_logo_key == '':
            ret_logo_key = ret_name

        list_location = []
        list_place_id = []
        if ret_address_info is not None:
            ret_address_json = json.loads(ret_address_info)
            if ret_address_json['status'] == 'OK':
                for i in range(len(ret_address_json['results'])):
                    list_location.append(ret_address_json['results'][i]['geometry']['location'])
                    list_place_id.append(ret_address_json['results'][i]['place_id'])

        if not list_location:
            return [ret_address, '', ret_logo_key, '', '']

        # get place details using place id
        max_score = 0
        for i in range(len(list_place_id)):
            ret_place = self.get_request_google_place_detail(list_place_id[i])
            ret_place_json = json.loads(ret_place)
            ret_place_address = ret_place_json["result"]["formatted_address"]
            score = fuzz.ratio(ret_address.lower(), ret_place_address.lower())
            max_score = max(max_score, score)

        if len(list_place_id) > 0 and max_score < 70:
            return ['', '', ret_logo_key, '', '']

        # get all buildings around position
        list_building_info = []
        for i in range(len(list_location)):
            ret_buildings = self.get_request_google_nearby([list_location[i]['lat'], list_location[i]['lng']])
            if ret_buildings is not None:
                ret_building_json = json.loads(ret_buildings)
                if ret_building_json['status'] == 'OK':
                    for j in range(len(ret_building_json['results'])):
                        list_building_info.append(ret_building_json['results'][j])

        # get best match result
        if not list_building_info:
            return [ret_address, '', ret_logo_key, '', '']

        max_score = 0
        max_building = None
        for i in range(len(list_building_info)):
            score = fuzz.ratio(ret_name.lower(), list_building_info[i]['name'].lower())
            if score >= max_score:
                max_score = score
                max_building = list_building_info[i]

        if max_score > 50:
            return [max_building['vicinity'],
                    max_building['icon'],
                    max_building['name'],
                    max_building['types'],
                    max_building['place_id']]
        else:
            return [ret_address, '', ret_logo_key, '', '']
