
from Categorization.GoogleOCR import GoogleOCR
from Categorization.FuncMl import FuncMl
import cv2


class Coordinates:

    def __init__(self):
        """
            class initial function
        """
        self.google_ocr = GoogleOCR()
        self.class_func = FuncMl()

    def get_data(self, ocr_json_page, img_page, coordinate_json, m_width, m_height):
        """
            if coordinate_json is None then get ocr text from whole page,
            or coordinate_json has value then get ocr tet from crop region of page.
        """
        # ------------------------- get the coordinate date from json -----------------------
        if coordinate_json is None:
            ocr_json = ocr_json_page
        elif ocr_json_page is None:
            ocr_json = None
        else:
            img_data = cv2.imread(img_page)
            height, width = img_data.shape[:2]

            if type(coordinate_json['x_1']) == int and type(coordinate_json['x_2']) == int:
                m_x1 = coordinate_json['x_1']
                m_x2 = coordinate_json['x_2']
            else:
                m_x1 = coordinate_json['x_1']/m_width
                m_x2 = coordinate_json['x_2']/m_width
                m_x1, m_x2 = min(m_x1, m_x2), max(m_x1, m_x2)
                m_x1 *= width
                m_x2 *= width

            if type(coordinate_json['y_1']) == int and type(coordinate_json['y_2']) == int:
                m_y1 = coordinate_json['y_1']
                m_y2 = coordinate_json['y_2']
            else:
                m_y1 = coordinate_json['y_1']/m_height
                m_y2 = coordinate_json['y_2']/m_height
                m_y1, m_y2 = min(m_y1, m_y2), max(m_y1, m_y2)
                m_y1 *= height
                m_y2 *= height

            crop_rect = [m_x1, m_y1, m_x2, m_y2]

            rate_x = float(width) / m_width
            rate_y = float(height) / m_height

            ocr_json = [{'description': ''}]
            new_text = ''
            rect_prev = None

            for i in range(1, len(ocr_json_page)):
                key_rect = self.class_func.get_rect_ocr_data(ocr_json_page, i)
                if self.class_func.check_contain_rect(crop_rect, key_rect):

                    ocr_json.append(ocr_json_page[i])

                    text_item = ocr_json_page[i]['description']
                    rect = ocr_json_page[i]['boundingPoly']['vertices']

                    x1 = self.class_func.get_field_int(rect[0], 'x')
                    y1 = self.class_func.get_field_int(rect[0], 'y')

                    if rect_prev is None:
                        x2 = 0
                        y2 = 0
                    else:
                        x2 = self.class_func.get_field_int(rect_prev[1], 'x')
                        y2 = self.class_func.get_field_int(rect_prev[0], 'y')

                    rect_prev = rect

                    if abs(x1 - x2) < rate_x / 5 and abs(y1 - y2) < rate_y / 30:
                        if text_item == '/' or (len(new_text) > 0 and new_text[-1] == '/'):
                            new_text += text_item
                        elif text_item == '-' or (len(new_text) > 0 and new_text[-1] == '-'):
                            new_text += text_item
                        elif text_item == '.' or (len(new_text) > 0 and new_text[-1] == '.'):
                            new_text += text_item
                        elif text_item == ',' or (len(new_text) > 0 and new_text[-1] == ','):
                            new_text += text_item
                        elif len(new_text) > 0 and new_text[-1] == '$':
                            new_text += text_item
                        else:
                            new_text += (' ' + text_item)
                    else:
                        if new_text == '':
                            new_text += text_item
                        else:
                            new_text += ('\n' + text_item)

            ocr_json[0]['description'] = new_text

        return ocr_json
