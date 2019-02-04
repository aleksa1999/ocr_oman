
from Categorization import FuncMl
from Categorization import FieldExtractor
from Categorization import constant
from receiptExtractors import ReceiptMerchantExtractor
from receiptExtractors import ReceiptAmountExtractor
import os


class ReceiptExtractor:

    def __init__(self):
        self.class_func = FuncMl()
        self.class_receipt_merchant = ReceiptMerchantExtractor()
        self.class_receipt_amount = ReceiptAmountExtractor()
        self.class_field_extractor = FieldExtractor()

        self.card_type = self.class_func.load_json(os.path.join(self.class_func.my_dir, 'config', 'card_type.json'))

        self.prev_ocr = None
        self.prev_name = None
        self.prev_type = None
        self.prev_address = None
        self.prev_remote_id = None

    def merchant_extract(self, img_file, ocr_json, ret_type):
        if self.prev_ocr == ocr_json:
            ret_address = self.prev_address
            ret_name = self.prev_name
            ret_type_list = self.prev_type
            ret_remote_id = self.prev_remote_id
        else:
            ret_merchant = self.class_receipt_merchant.extract(filename=img_file, ocr_json=ocr_json)
            [ret_address, _, ret_name, ret_type_list, ret_remote_id] = ret_merchant
            if len(ret_name) > 50:
                ret_name = None
            self.prev_ocr = ocr_json
            self.prev_address = ret_address
            self.prev_remote_id = ret_remote_id
            self.prev_name = ret_name
            self.prev_type = ret_type_list

        if ret_type == 'address':
            return ret_address
        elif ret_type == 'name':
            return ret_name
        elif ret_type == 'type_list':
            return ret_type_list
        elif ret_type == 'remote_id':
            return ret_remote_id
        else:
            return None

    def extract_address(self, filename, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret = self.merchant_extract(img_list[0], ocr_json, 'address')

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return ret

    def extract_remote_id(self, filename, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret = self.merchant_extract(img_list[0], ocr_json, 'remote_id')

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return ret

    def extract_remote_categories(self, filename, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret = self.merchant_extract(img_list[0], ocr_json, 'type_list')

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return ret

    def get_card_info(self, ocr_json):
        card_type = None
        card_pos_list = []

        for i in range(1, len(ocr_json) - 1):
            text1 = ocr_json[i]['description']
            text2 = ocr_json[i]['description'] + ' ' + ocr_json[i + 1]['description']

            for card in self.card_type:
                if text1.upper() in self.card_type[card]:
                    card_pos_list.append(i + 1)
                    card_type = card
                    break
                elif text2.upper() in self.card_type[card]:
                    card_pos_list.append(i + 2)
                    card_type = card
                    break

        return card_type, card_pos_list

    def extract_card_type(self, filename, ocr_json=None):
        # ------------------ Get ocr data and remove temp file ----------------
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        # ------------------------Extract the card type ------------------------
        card_type, _ = self.get_card_info(ocr_json)

        return card_type

    def extract_card_number(self, filename, ocr_json=None):
        # ------------------ Get ocr data and remove temp file ----------------
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        # --------------------- Extract the Card Number -----------------------
        for i in range(1, len(ocr_json)):
            text = ocr_json[i]['description']

            if len(text) > 11 and text[-4:].isdigit():
                text_front = ''.join(set(text[1:-5]))

                if text_front == 'X' or text_front == 'x' or text_front == '*':
                    return text[-4:]

            if i > 10 and len(text) == 4 and text.isdigit():      # '* * * * * 4075'
                f_num = True
                for j in range(i - 10, i):
                    if ocr_json[j]['description'] != '*':
                        f_num = False

                if f_num:
                    return text

            if i > 3 and len(text) == 4 and text.isdigit():      # 'XXXX XXXX XXXX 4075'
                f_num = True
                for j in range(i - 3, i):
                    if ocr_json[j]['description'] != 'XXXX':
                        f_num = False

                if f_num:
                    return text

            if i > 3 and len(text) == 4 and text.isdigit():      # 'ending in 4075'
                if ocr_json[i-2]['description'] == 'ending' and ocr_json[i-1]['description'].lower() == 'in':
                    return text

        # ---------------- Special case - 'Visa 2345 (Swipe)'------------------
        card_type, card_pos_list = self.get_card_info(ocr_json)

        if card_type is None:
            return None

        for card_pos in card_pos_list:
            # Check text for card number
            if len(ocr_json[card_pos]['description']) == 4 and ocr_json[card_pos]['description'].isdigit():
                # Check region
                rect1 = self.class_func.get_rect_ocr_data(ocr_json, card_pos - 1)
                rect2 = self.class_func.get_rect_ocr_data(ocr_json, card_pos)

                if rect1[0] + rect2[0] < 2 * rect1[2] and abs(rect1[1] - rect2[1]) < int((rect1[3] - rect1[1]) / 2):
                    return ocr_json[card_pos]['description']

        return None

    def extract_field(self, filename, field_id, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret = None

        if field_id == constant.RECEIPT_MERCHANT_ID:
            ret = self.merchant_extract(img_list[0], ocr_json, 'name')

        elif field_id == constant.RECEIPT_AMOUNT_ID:
            ret = self.class_receipt_amount.extract(img_list[0], ocr_json)

        elif field_id == constant.RECEIPT_TAX_ID:
            hint_list = [
                [["proximity", {"type": "same_line_prefix", "text": "SALES TAX"}]],
                [["proximity", {"type": "same_line_suffix", "text": "TAX CA"}]],
                [["proximity", {"type": "same_line_prefix", "text": "TAX DUE"}]],
                [["proximity", {"type": "same_line_prefix", "text": "Tax"}]]
            ]

            profile_hash = {u'width': 8.5, u'height': 11}
            field_hint = {"data_type": 'currency', "hints": hint_list}
            ret = self.class_field_extractor.extract_v2(img_list[0], profile_hash, field_hint, en_fuzzy=False,
                                                        ocr_json_data=ocr_json)
            ret = ret[0]['value']

        elif field_id == constant.RECEIPT_DATE_ID:
            hint_list = [
                [["proximity", {"type": "same_line_prefix", "text": "Credit Purchase"}]],
                []
            ]

            profile_hash = {u'width': 8.5, u'height': 11}
            field_hint = {"data_type": 'date', "hints": hint_list}
            ret = self.class_field_extractor.extract_v2(img_list[0], profile_hash, field_hint, en_fuzzy=False,
                                                        ocr_json_data=ocr_json, select_first=True)
            ret = ret[0]['value']

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return {"field_id": field_id, "value": ret}

    def extract(self, filename, ocr_json=None):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if ocr_json is None:
            if json_list and json_list[0] is not None:
                ocr_json = self.class_func.merge_ocr_json(json_list)
            else:
                ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret_extract = []
        for i in range(6):
            ret_field = self.extract_field(img_list, i + 1, ocr_json)
            ret_extract.append(ret_field)

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return ret_extract

    def extract_all_info(self, filename):
        img_list, temp_list, json_list = self.class_func.get_img_list(filename)

        if json_list and json_list[0] is not None:
            ocr_json = self.class_func.merge_ocr_json(json_list)
        else:
            ocr_json = self.class_func.get_json_google_from_jpg(img_list[0])

        ret_fields = self.extract(img_list[0], ocr_json)
        ret_address = self.extract_address(img_list[0], ocr_json)
        ret_card_type = self.extract_card_type(img_list[0], ocr_json)
        ret_card_number = self.extract_card_number(img_list[0], ocr_json)
        ret_remote_id = self.extract_remote_id(img_list[0], ocr_json)
        ret_remote_categories = self.extract_remote_categories(img_list[0], ocr_json)

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        ret = {'date': ret_fields[0]['value'],
               'amount': ret_fields[1]['value'],
               'merchant': ret_fields[4]['value'],
               # 'tax': ret_fields[5]['value'],
               'address': ret_address,
               # 'card_type': ret_card_type,
               # 'card_number': ret_card_number,
               # 'remote_id': ret_remote_id,
               # 'remote_categories': ret_remote_categories
               }

        return ret
