
from datetime import datetime
import numpy as np
import cv2
import json
import os
import csv
import pdf2jpg
import base64
import httplib


class FuncMl:
    def __init__(self):
        """
            Constructor for the class
        """
        self.my_dir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.google_key = self.load_text(os.path.join(self.my_dir, 'config', 'vision_key.txt'))

    @staticmethod
    def load_json(filename):
        json_file = open(filename)
        json_data = json.load(json_file)
        return json_data

    @staticmethod
    def load_csv(filename):
        """
            load the csv data and return it.
        """
        if os.path.isfile(filename):
            file_csv = open(filename, 'rb')
            reader = csv.reader(file_csv)
            data_csv = []
            for row_data in reader:
                data_csv.append(row_data)

            file_csv.close()
            return data_csv
        else:
            return None

    @staticmethod
    def save_csv(filename, data):
        """
            save the "data" to filename as csv format.
        """
        file_out = open(filename, 'wb')
        writer = csv.writer(file_out)
        writer.writerows(data)
        file_out.close()

    @staticmethod
    def load_text(filename):
        if os.path.isfile(filename):
            file1 = open(filename, 'r')
            text = file1.read()
            file1.close()
        else:
            text = ''

        return text

    @staticmethod
    def save_text(filename, text):
        file1 = open(filename, 'w')
        file1.write(text)
        file1.close()

    def load_receipt_json(self):
        """
            load the standard base documents json file and return the folder and display name of categories.
        """
        standard_data = self.load_json(os.path.join(self.my_dir, "config/receipt_categories.json"))
        cat_folder = []
        cat_id = []

        for cat_name in standard_data:
            cat_folder.append(cat_name)
            cat_id.append(standard_data[cat_name]["id"])

        return standard_data, cat_folder, cat_id

    def load_receipt_amt_keys(self):
        csv_data = self.load_csv(os.path.join(self.my_dir, "config/receipt_amount_keys.csv"))
        ret_keys = []
        for i in range(len(csv_data)):
            ret_keys.append(csv_data[i][0])

        csv_data = self.load_csv(os.path.join(self.my_dir, "config/receipt_amount_no_keys.csv"))
        ret_no_keys = []
        for i in range(len(csv_data)):
            ret_no_keys.append(csv_data[i][0])

        return ret_keys, ret_no_keys

    def load_vendor_profile(self, type):
        """
            load the vendor profile jsons
        """
        if type == 'vendor':
            json_data = self.load_json(os.path.join(self.my_dir, "config/vendor_profile_NL.json"))
        elif type == 'passport':
            json_data = self.load_json(os.path.join(self.my_dir, "config/passport_profile.json"))
        else:
            json_data = {}

        return json_data

    @staticmethod
    def get_file_list(root_dir):
        """
            get all files in root_dir directory
        """
        path_list = []
        file_list = []
        join_list = []
        for path, _, files in os.walk(root_dir):
            for name in files:
                path_list.append(path)
                file_list.append(name)
                join_list.append(os.path.join(path, name))

        return path_list, file_list, join_list

    def __multipdf2image(self, filename, page=0, max_pdf_page=10):
        """
            In case of multi page pdf file, convert to multi jpg files and add to image and temp list.
            In case of general image file, add to only image list.
        """
        img_list = []
        temp_list = []
        json_list = []

        if self.get_ext(filename) == "PDF":
            temp_pdf = "temp_pdf" + str(datetime.now().microsecond)
            pdf_cnt = pdf2jpg.pdf2jpg_ppm(filename, temp_pdf, page, max_pdf_page)

            for j in range(pdf_cnt):
                img_name = temp_pdf + str(j) + '.jpg'
                temp_name = self.limit_image_size(img_name, 4000000)
                temp_list.append(img_name)
                temp_list.append(temp_name)
                rot_st, rot_name, ocr_json = self.rotate_img(temp_name)

                if temp_name != rot_name:
                    temp_list.append(rot_name)

                if rot_st:
                    img_list.append(rot_name)
                    json_list.append(ocr_json)
                else:
                    img_list.append(img_name)
                    json_list.append(None)

        else:
            temp_name = self.limit_image_size(filename, 4000000)

            if temp_name != filename:
                temp_list.append(temp_name)

            rot_st, rot_name, ocr_json = self.rotate_img(temp_name)

            if temp_name != rot_name:
                temp_list.append(rot_name)

            if rot_st:
                img_list.append(rot_name)
                json_list.append(ocr_json)
            else:
                img_list.append(filename)
                json_list.append(None)

        return img_list, temp_list, json_list

    @staticmethod
    def rm_file(filename):
        if os.path.isfile(filename):
            os.remove(filename)

    @staticmethod
    def get_ext(filename):
        """
            get the file extension and return it as upper case style.
        """
        return filename.split(".")[-1].upper()

    @staticmethod
    def remove_duplicate(list_data):
        """
            remove the duplication from list_data and return result
        """
        return list(set(list_data))

    @staticmethod
    def limit_image_size(img_name, limit_size):
        """
            if size of image is bigger than limit_size, reduce the image resolution.
        """
        img = cv2.imread(img_name)
        height, width = img.shape[:2]
        max_size = limit_size * 2
        temp_name = "temp_jpg" + str(datetime.now().microsecond) + '.jpg'

        if height * width > max_size:
            rate = np.sqrt(float(height * width) / max_size)
            temp_img = cv2.resize(img, (int(float(width) / rate), int(float(height) / rate)),
                                  interpolation=cv2.INTER_LINEAR)
            cv2.imwrite(temp_name, temp_img)
            return temp_name

        elif os.path.getsize(img_name) > limit_size:
            temp_img = img

            cv2.imwrite(temp_name, temp_img)
            return temp_name

        else:
            return img_name

    @staticmethod
    def text_clean(text):
        return text.strip('-/,.()')

    @staticmethod
    def conv_str(text):
        str_text = ''
        conv_table = {u'\u0422': 'T',
                      u'\u0410': 'A',
                      u'\u0425': 'X',
                      u'\u0430': 'a',
                      u'\u0445': 'x'}
        for i in range(len(text)):
            try:
                if text[i] in conv_table:
                    s = conv_table[text[i]]
                else:
                    s = str(text[i]).encode('ASCII')

                str_text += s
            except:
                pass

        return str_text

    @staticmethod
    def get_field_int(dict_data, field):
        if field in dict_data:
            return dict_data[field]
        else:
            return 0

    @staticmethod
    def check_overlap_rect(rect1, rect2):
        min_x1 = min(rect1[0], rect1[2])
        max_x1 = max(rect1[0], rect1[2])
        min_y1 = min(rect1[1], rect1[3])
        max_y1 = max(rect1[1], rect1[3])

        min_x2 = min(rect2[0], rect2[2])
        max_x2 = max(rect2[0], rect2[2])
        min_y2 = min(rect2[1], rect2[3])
        max_y2 = max(rect2[1], rect2[3])

        if max_x1 < min_x2 or max_x2 < min_x1 or max_y1 < min_y2 or max_y2 < min_y1:
            return False
        else:
            return True

    @staticmethod
    def merge_rect(rect1, rect2):
        if rect1 is None and rect2 is not None:
            return rect2
        elif rect1 is not None and rect2 is None:
            return rect1
        elif rect1 is None and rect2 is None:
            return None
        else:
            return [min(rect1[0], rect2[0]), min(rect1[1], rect2[1]), max(rect1[2], rect2[2]), max(rect1[3], rect2[3])]

    @staticmethod
    def check_contain_rect(big_rect, small_rect):
        min_x1 = min(big_rect[0], big_rect[2])
        max_x1 = max(big_rect[0], big_rect[2])
        min_y1 = min(big_rect[1], big_rect[3])
        max_y1 = max(big_rect[1], big_rect[3])

        min_x2 = min(small_rect[0], small_rect[2])
        max_x2 = max(small_rect[0], small_rect[2])
        min_y2 = min(small_rect[1], small_rect[3])
        max_y2 = max(small_rect[1], small_rect[3])

        if min_x1 < min_x2 < max_x2 < max_x1 and min_y1 < min_y2 < max_y2 < max_y1:
            return True
        else:
            return False

    @staticmethod
    def dict_int(dict_parent, element):
        if element in dict_parent:
            return dict_parent[element]
        else:
            return 0

    def get_rect_ocr_data(self, ocr_data, ind):
        p = ocr_data[ind]['boundingPoly']['vertices']
        rect = [self.dict_int(p[0], 'x'), self.dict_int(p[0], 'y'), self.dict_int(p[1], 'x'), self.dict_int(p[2], 'y')]

        return rect

    def get_img_orientation_google(self, img_name):
        ret_json = self.get_json_google_from_jpg(img_name)

        if ret_json is None:
            return '0', None

        orient_list = [0, 0, 0, 0]
        for i in range(1, len(ret_json)):
            orient_list[self.check_word_orient(ret_json[i]['boundingPoly']['vertices'])] += 1

        return str(np.argmax(orient_list) * 90), ret_json

    @staticmethod
    def check_word_orient(word_corner_list):
        """
            word_corner_list example:
            [{u'y': 1056, u'x': 2535}, {u'y': 1485, u'x': 2527}, {u'y': 1484, u'x': 2457}, {u'y': 1055, u'x': 2465}]
        """
        if 'x' in word_corner_list[0]:
            x1 = word_corner_list[0]['x']
        else:
            return 0

        if 'y' in word_corner_list[0]:
            y1 = word_corner_list[0]['y']
        else:
            return 0

        if 'x' in word_corner_list[2]:
            x3 = word_corner_list[2]['x']
        else:
            return 0

        if 'y' in word_corner_list[2]:
            y3 = word_corner_list[2]['y']
        else:
            return 0

        dx = x3 - x1
        dy = y3 - y1

        if dx >= 0:
            if dy >= 0:
                return 0
            else:
                return 3
        else:
            if dy >= 0:
                return 1
            else:
                return 2

    def rotate_img(self, img_name):
        img_orient, ocr_json = self.get_img_orientation_google(img_name)

        if ocr_json is None:
            return False, img_name, None

        img_jpg = cv2.imread(img_name)
        temp_image = "temp_img" + str(datetime.now().microsecond) + '.jpg'

        if img_orient == '0':
            rot_img = img_jpg

        else:
            if img_orient == '90':
                rots = 1
            elif img_orient == '180':
                rots = 2
            elif img_orient == '270':
                rots = 3
            else:
                rots = 0

            rot_img = np.rot90(img_jpg, rots)
            ocr_json = None

        cv2.imwrite(temp_image, rot_img)

        return True, temp_image, ocr_json

    @staticmethod
    def __make_request_json(img_file, output_filename, detection_type='text'):

        # Read the image and convert to json
        with open(img_file, 'rb') as image_file:
            # content_json_obj = {'content': base64.b64encode(image_file.read()).decode('UTF-8')}
            content_json_obj = {'content': base64.b64encode(image_file.read())}

        if detection_type == 'text':
            feature_json_arr = [{'type': 'TEXT_DETECTION'}, {'type': 'DOCUMENT_TEXT_DETECTION'}]
        elif detection_type == 'logo':
            feature_json_arr = [{'type': 'LOGO_DETECTION'}]
        else:
            feature_json_arr = [{'type': 'TEXT_DETECTION'}, {'type': 'DOCUMENT_TEXT_DETECTION'}]

        request_list = {'features': feature_json_arr, 'image': content_json_obj}

        # Write the object to a file, as json
        with open(output_filename, 'w') as output_json:
            json.dump({'requests': [request_list]}, output_json)

    def __get_text_info(self, json_file, detection_type='text'):

        data = open(json_file, 'rb').read()
        try:
            import requests

            response = requests.post(
                url='https://vision.googleapis.com/v1/images:annotate?key=' + self.google_key,
                data=data,
                headers={'Content-Type': 'application/json'})

            ret_json = json.loads(response.text)
            ret_val = ret_json['responses'][0]

            if detection_type == 'text' and 'textAnnotations' in ret_val:
                return ret_val['textAnnotations']
            elif detection_type == 'logo' and 'logoAnnotations' in ret_val:
                return ret_val['logoAnnotations']
            else:
                return None

        except Exception as e:
            return None

    def __get_google_request(self, json_file, detection_type='text'):

        data = open(json_file, 'rb').read()

        conn = httplib.HTTPSConnection("vision.googleapis.com")
        conn.request("POST", "/v1/images:annotate?key=" + self.google_key, body=data)
        response = conn.getresponse()

        ret_json = json.loads(response.read())
        ret_val = ret_json['responses'][0]

        conn.close()

        if detection_type == 'text' and 'textAnnotations' in ret_val:
            return ret_val['textAnnotations']
        elif detection_type == 'logo' and 'logoAnnotations' in ret_val:
            return ret_val['logoAnnotations']
        else:
            return None

    def get_json_google_from_jpg(self, img_file, detection_type='text'):

        temp_json = "temp" + str(datetime.now().microsecond) + '.json'

        # --------------------- Image crop and rescaling, then ocr ------------------
        if img_file is None:
            ret_json = None
        else:
            self.__make_request_json(img_file, temp_json, detection_type)
            # ret_json = self.__get_text_info(temp_json, detection_type)
            ret_json = self.__get_google_request(temp_json, detection_type)

        # --------------------- delete temporary files -------------------------------
        self.rm_file(temp_json)

        if ret_json is not None and detection_type == 'text':
            # for i in range(len(ret_json)):
            #     ret_json[i]['description'] = self.conv_str(ret_json[i]['description'])

            self.save_text('a_ocr.txt', ret_json[0]['description'].encode('utf8'))

        return ret_json

    def get_img_list(self, src, pdf_page=0):
        """
            Return image and temp list from image file or image list
        """
        temp_list = []
        json_list = []

        if type(src).__name__ == 'list':
            img_list = src
        elif src.startswith('temp_'):
            img_list = [src]
        else:
            img_list, temp_list, json_list = self.__multipdf2image(src, page=pdf_page)

        return img_list, temp_list, json_list

    @staticmethod
    def merge_ocr_json(json_list):
        """
            Merge ocr_json list into 1 json and return it.
        """
        ret_json = []
        first_page = 0
        h = 0

        for first_page in range(len(json_list)):
            if json_list[first_page] is not None:
                h = json_list[first_page][0]['boundingPoly']['vertices'][2]['y']

                for i in range(len(json_list[first_page])):
                    ret_json.append(json_list[first_page][i])

                break

        for i in range(first_page + 1, len(json_list)):
            if json_list[i] is not None:
                new_h = json_list[i][0]['boundingPoly']['vertices'][2]['y']
                ret_json[0]['description'] += ('\n' + json_list[i][0]['description'])
                ret_json[0]['boundingPoly']['vertices'][2]['y'] += new_h
                ret_json[0]['boundingPoly']['vertices'][3]['y'] += new_h

                for j in range(1, len(json_list[i])):
                    new_item = json_list[i][j]
                    new_item['boundingPoly']['vertices'][0]['y'] += h
                    new_item['boundingPoly']['vertices'][1]['y'] += h
                    new_item['boundingPoly']['vertices'][2]['y'] += h
                    new_item['boundingPoly']['vertices'][3]['y'] += h
                    ret_json.append(new_item)

                h += new_h

        return ret_json

    def get_line_rect(self, ocr_json):
        """
            Get the rect of each lines of OCR
        """
        ocr_text = ocr_json[0]['description']
        text_lines = ocr_text.splitlines()

        temp_rect = None
        ret = {'text': [ocr_text], 'rect': [self.get_rect_ocr_data(ocr_json, 0)]}

        pos_start = 1
        for i in range(len(text_lines)):
            f_match = False

            for j in range(pos_start, len(ocr_json)):
                temp_text = ''
                temp_rect = None

                for k in range(j, min(j + 10, len(ocr_json))):
                    temp_text += ocr_json[k]['description']
                    new_rect = self.get_rect_ocr_data(ocr_json, k)
                    temp_rect = self.merge_rect(temp_rect, new_rect)

                    if temp_text == text_lines[i].replace(' ', ''):
                        f_match = True
                        pos_start = k + 1
                        break

                if f_match:
                    break

            ret['text'].append(text_lines[i])
            ret['rect'].append(temp_rect)

        return ret

    def remove_vertical_text(self, ocr_json):
        """
            Remove vertical text from ocr_json and return it.
        """
        ocr_text = ocr_json[0]['description']
        new_ocr_text = ''
        j = 0

        for i in range(1, len(ocr_json)):
            word_orient = self.check_word_orient(ocr_json[i]['boundingPoly']['vertices'])
            word_text = ocr_json[i]['description']

            j += len(word_text)
            word_between = ocr_text[j]

            if word_between == '\n' or word_between == ' ':
                j += 1
            else:
                word_between = ''

            if word_orient == 0:
                if word_text == '' and word_between == '\n':
                    pass
                else:
                    new_ocr_text += word_text + word_between

        return new_ocr_text

    @staticmethod
    def check_same_line(rect1, rect2):
        """
            Check rect1 and rect2 is same line and return result
        """
        if rect1[1] <= rect2[1] <= rect1[3]:
            return True
        elif rect2[1] <= rect1[1] <= rect2[3]:
            return True
        else:
            return False

    @staticmethod
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
