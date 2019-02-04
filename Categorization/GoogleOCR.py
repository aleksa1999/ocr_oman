
from FuncMl import FuncMl


class GoogleOCR:

    def __init__(self):
        """
            class initial function
        """
        self.class_func = FuncMl()

    def get_text_google(self, img_file, pdf_page=0):
        """
            Get text from pdf/image file from range of pdf_page
        """
        img_list, temp_list, json_list = self.class_func.get_img_list(img_file, pdf_page=pdf_page)
        ret_text = ''

        # ----------------- Image crop and rescaling, then ocr ----------------
        for img_ind in range(len(img_list)):

            if json_list and json_list[img_ind] is not None:
                img_json = json_list[img_ind]
            else:
                img_json = self.class_func.get_json_google_from_jpg(img_list[img_ind])

            if img_json is None:
                ocr_text = ''
            else:
                ocr_text = img_json[0]['description']

            ret_text += ocr_text

        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        self.class_func.save_text('a_ocr.txt', ret_text)

        return ret_text

    def get_json_google(self, img_file, detection_type='text'):
        """
            Get the ocr json from first page of document
        """
        img_list, temp_list, json_list = self.class_func.get_img_list(img_file, pdf_page=1)

        if detection_type == 'text' and json_list and json_list[0] is not None:
            ret_json = json_list[0]
        else:
            ret_json = self.class_func.get_json_google_from_jpg(img_list[0], detection_type)

        # --------------------- delete temporary files ------------------------
        for temp_file in temp_list:
            self.class_func.rm_file(temp_file)

        return ret_json
