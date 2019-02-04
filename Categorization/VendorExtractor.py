
from Categorization import FuncMl
from Categorization import FieldExtractor
from Categorization import TextExtractor
from datetime import datetime


class VendorExtractor:

    def __init__(self, mode='vendor', country='US'):
        self.class_func = FuncMl()
        self.class_field_extractor = FieldExtractor()
        self.class_text_extractor = TextExtractor()

        self.country = country
        self.mode = mode

        self.vendor_profile_list = self.class_func.load_vendor_profile(mode)
        if mode == 'vendor':
            self.vendor_profile = self.vendor_profile_list['VENDOR1']
        elif mode == 'passport':
            self.vendor_profile = self.vendor_profile_list['PASSPORT1']

    def extract(self, filename, field_id=None, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        result = []

        if ocr_json is None:
            return result
        else:
            ret_json = self.class_func.get_line_rect(ocr_json)
            ocr_text_lines, ocr_rect_lines = ret_json['text'], ret_json['rect']

        for hint_hash in self.vendor_profile['fields']:
            if field_id is None or hint_hash['field_id'] == field_id:
                if 'key_type' in hint_hash:
                    key_type = hint_hash['key_type']
                else:
                    key_type = ''

                ret_val_text = self.class_text_extractor.extract_v1(ocr_text_lines,
                                                                    ocr_rect_lines,
                                                                    hint_hash["data_type"],
                                                                    hint_hash["keys"],
                                                                    key_type)

                if ret_val_text is None:
                    ret_field = None
                    ret_field = self.class_field_extractor.extract_v2(img_list[0], self.vendor_profile, [hint_hash],
                                                                      ocr_json_data=ocr_json,
                                                                      en_fuzzy=False,
                                                                      country=self.country)[0]
                else:
                    ret_field = {'field_id': hint_hash["field_id"],
                                 'field_name': hint_hash['name'],
                                 'value': ret_val_text}

                result.append(ret_field)

        if self.mode == 'vendor':
            ret_section = []
            for i in range(len(ocr_text_lines)):
                text_line = ocr_text_lines[i]
                if len(text_line) > 6 and text_line[:6].isdigit() and text_line[6] == ':' and text_line[:6] not in ret_section:
                    ret_section.append(text_line[:6])

            ret_field = {'field_id': 0,
                         'field_name': 'Section',
                         'value': ret_section}
            result.append(ret_field)

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return result

    def get_date_mrp(self, text, mode='birth'):
        yy = text[:2]
        mm = text[2:4]
        dd = text[4:]

        if mode == 'expire':
            yy = '20' + yy
        elif mode == 'birth':
            cur_y = str(datetime.today().year)[2:]
            if int(yy) < int(cur_y):
                yy = '20' + yy
            else:
                yy = '19' + yy

        return yy + '-' + mm + '-' + dd

    def extract_MRP(self, filename, ocr_json=None, mode='passport'):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        result = []

        if ocr_json is None:
            return result
        else:
            ret_json = self.class_func.get_line_rect(ocr_json)
            ocr_text_lines, ocr_rect_lines = ret_json['text'], ret_json['rect']

        line1 = ''
        line2 = ''
        for i in range(len(ocr_text_lines) - 1):
            if ocr_text_lines[i].count('<') > 4 and ocr_text_lines[i + 1].count('<') > 4:
                line1 = ocr_text_lines[i]
                line2 = ocr_text_lines[i + 1]
                break

        if line1 == '':
            return result

        line1 = line1.replace(' ', '')
        line2 = line2.replace(' ', '')

        if len(line1) != 44 or len(line2) != 44:
            return result

        # print line1
        # print line2

        if mode == 'passport':
            if line1[0] != 'P':
                if line2[0] == 'P':
                    line1, line2 = line2, line1
                else:
                    return result

        ret_type = line1[1]
        ret_country = line1[2:5]
        ret_name = line1[5:]

        if ret_type != '<':
            result.append({'field_name': 'Type', 'value': ret_type})

        result.append({'field_name': 'Country', 'value': ret_country})

        ret_name = ret_name.replace('<', ' ').strip()
        if ret_name.__contains__('  '):
            result.append({'field_name': 'Surname', 'value': ret_name.split('  ')[0]})
            result.append({'field_name': 'Given name', 'value': ret_name.split('  ')[1]})
        else:
            result.append({'field_name': 'Full Name', 'value': ret_name})

        ret_no = line2[:9]
        ret_national = line2[10:13]
        ret_date_birth = line2[13:19]
        ret_sex = line2[20]
        ret_date_expire = line2[21:27]
        ret_personal = line2[28:42]
        # print ret_no
        ret_no = ret_no.replace('<', '')
        result.append({'field_name': 'Passport Number', 'value': ret_no})

        # print ret_national
        ret_national = ret_national.replace('<', '')
        if ret_national != '':
            result.append({'field_name': 'Nationality', 'value': ret_national})

        result.append({'field_name': 'Date of Birth', 'value': self.get_date_mrp(ret_date_birth, 'birth')})
        result.append({'field_name': 'Date of Expire', 'value': self.get_date_mrp(ret_date_expire, 'expire')})

        if ret_sex != '<':
            result.append({'field_name': 'Sex', 'value': ret_sex})

        ret_personal = ret_personal.replace('<', '')
        result.append({'field_name': 'Personal Number', 'value': ret_personal})

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return result
