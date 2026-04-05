import tcms_api
import base64
import os
import xmlrpc.client
import ssl
import sys
import time
import requests
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import traceback
from datetime import datetime

TCMS_HOST = "{YOUR HOST NAME OR IP}"            # Kiwi TCMS Host
TCMS_API = "/xml-rpc/"                          # Kiwi TCMS API Path
TCMS_HOST_LOGIN = "{YOUR ADMIN LOGIN NAME}"     # Admin login
TCMS_HOST_PASS = "{YOUR ADMIN PASSWORD}"        # Admin pass
SSL_Verify = False                              # Disabling SSL Verify
TCMS_TYPE_ID = 0
TCMS_TYPE_NAME = 'plan'

SSLVerifying = input('Включить проверку SSL / Is need to verify SSL? y/n or Enter to NO (default) ')
if SSLVerifying == 'y':
    SSL_Verify = True

if SSL_Verify:
    pass
else:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # отключание сообщений типа warning, если проверка SSL отключена
    # Использование проверки SSL
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:        
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


print('Инициализация клиента / Init client...')
TCMS_HOST_API = TCMS_HOST + TCMS_API
try:
    rpc = tcms_api.TCMS(TCMS_HOST_API, TCMS_HOST_LOGIN, TCMS_HOST_PASS).exec
    test_plans = rpc.TestPlan.filter({})        
    print("Инициализация клиента - успешно/ Client init success")
    
    for plan in test_plans:
            print(f"ID: {plan['id']}, Name: {plan['name']}")

    showTestPlanCases = input('Показать кейсы плана / Show plan test-cases? {input number} or Enter to pass ')
    try:
        TestPlanCases = int(showTestPlanCases)
        test_cases = rpc.TestCase.filter({TCMS_TYPE_NAME: TestPlanCases})
        for test_case in test_cases:
            case_id = test_case['id']            
            case_summary = test_case['summary']
            print(f"# Кейс ID: {case_id} - {case_summary}")
    except:
        pass

    try:
        TCMS_TYPE_ID = int(input('Введите номер тест-плана / Input test-plan ID: '))
    except:
        pass
       
    test_cases = rpc.TestCase.filter({TCMS_TYPE_NAME: TCMS_TYPE_ID}) # 1. Находим нужные кейсы по ID тест-плана
    isNeedToSaveText = input('Нужно сохранять текст в файл / Is needed to save texts? y/n or Enter to YES (default)') or "y"
    isNeedToSaveAttachments = input('Нужно сохранять вложения / Is needed to save attachments? y/n or Enter to YES (default)') or "y"
    caseURLreplace = TCMS_HOST + "/case/"
    caseURLdefaultPalceholder = 'кейс № '
    isNeedToRenameURLtoNAME = input(f"Нужно заменять ссылки вида {caseURLreplace} на слово {caseURLdefaultPalceholder} / Is needed to rename URLs {caseURLreplace} to text {caseURLdefaultPalceholder}? y/n or <Enter> to YES (default)") or "y"
    if isNeedToRenameURLtoNAME == 'y':
        caseURLpalceholder = input(f"Меняем {caseURLreplace} на ...? по умолчанию {caseURLdefaultPalceholder}. Введите текст или нажмите Enter / Input paceholder name or <Enter> for {caseURLdefaultPalceholder} (default)") or f"caseURLdefaultPalceholder"        
    isNeedToRenameAttachments = input('Нужно переименовывать вложения / Is needed to rename attachments? y/n or <Enter> to YES (default)') or "y"
    if isNeedToSaveAttachments == 'y':        
        saveFilesByCasesFolder = input('Нужно разложить файлы кейсов по папкам / Is needed to save attachments in TC folders? y/n or <Enter> to NO (default)') or "n"
    lenTC = len(test_cases)
    countTC = 1
    attachTC =0
    files = {}
    txtfilename = 'output_' + str(TCMS_TYPE_NAME) + '_' + str(TCMS_TYPE_ID) + '_' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.txt'
    print(f"Вывод кейсов в файл {txtfilename}")
    with open(txtfilename, "w") as f:
         f.write('')
    TCAttachementsDownloadedCounter = 0
    for case in test_cases:
        case_id = case['id']   
        case_text = case['text']

        if isNeedToSaveText == 'y':        
            original_stdout = sys.stdout # Save the original stdout
            with open(txtfilename, 'a', encoding='cp1251', errors='ignore') as f:
                sys.stdout = f         # Redirect standard output to the file
                print(f"# Кейс ID: {case_id} - {case['summary']}")
                case_text = case_text.replace(' ~~','~~')
                case_text = case_text.replace('~~ ','~~')
                case_text = case_text.replace('*~~','* ~~')
                case_text = case_text.replace('\~~', '\ ~~')
                case_text = case_text.replace('~~\\', '~~ \\')
                case_text = case_text.replace(':~~',': ~~')
                if isNeedToRenameURLtoNAME == 'y':
                    case_text = case_text.replace(caseURLreplace, caseURLpalceholder)
                print(case_text)
                sys.stdout = original_stdout # Reset standard output to the console
        print('Обработан кейс', case_id, '. ', countTC ,' из ', lenTC)            
        countTC += 1

        # 2. Получаем список вложений
        attachments = rpc.TestCase.list_attachments(case_id)
        
        
        if attachments != None and isNeedToSaveText == 'y':
            original_stdout = sys.stdout # Save the original stdout            
            with open(txtfilename, 'a', encoding='cp1251', errors='ignore') as f:
                sys.stdout = f         # Redirect standard output to the file
                print('')
                print("### Вложения кейса № ", case_id)
                print('')
                sys.stdout = original_stdout # Reset standard output to the console
        
        attchmentLocalCounter = 0
        for attach in attachments:
            
            attachmentURL = attach['url']
            filename = attachmentURL
            filename = filename.replace(TCMS_HOST + '/uploads/attachments/auth_user/','')
            filename = filename.replace(TCMS_HOST + '/uploads/attachments/testcases_testcase/','')
            folder = ''
            for i in filename:
                if i != '/': folder += i
                else: break
            filename = filename.replace(folder + '/','')            
            print(f" Кейс: {case_id} Имя файла: {filename} URL: {attachmentURL}")
            attachTC +=1
            attchmentLocalCounter += 1

            # сохранение новых имен в словарь files
            if isNeedToRenameAttachments == 'y':
                fileExtension = Path(filename).suffix        
                relativeAttachmentURL = attachmentURL.replace(TCMS_HOST,'')
                formattedCaseId = f"{case_id:05}"
                formattedAttachId = f"{attachTC:010}"        
                replacedFilename = 'tc_' + formattedCaseId + '_fileid_' + formattedAttachId + fileExtension        
                files.update({relativeAttachmentURL: [filename,replacedFilename]})
                filename = replacedFilename # замена имени файла
            
            # сохранение вложений
            if isNeedToSaveAttachments == 'y':
                if saveFilesByCasesFolder == 'y':
                    filesFolder = f"files_{txtfilename}_{case_id:05}"
                else:                    
                    filesFolder = f"files_{txtfilename}"

                os.makedirs(filesFolder, exist_ok=True)
                
                save_path = filesFolder + '/' + filename # сохранение в папку files
                with requests.get(attachmentURL, stream = True, verify = SSL_Verify) as r:
                    r.raise_for_status() # Проверяем, что запрос прошел успешно
                    # 2. Открываем локальный файл для бинарной записи
                    with open(save_path, 'wb') as f:
                        # 3. Читаем данные частями (chunk)
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                print(f'Файл скачан и сохранен как: {filename}')
                TCAttachementsDownloadedCounter +=1

            if isNeedToSaveText == 'y':
                original_stdout = sys.stdout # Save the original stdout
                with open(txtfilename, 'a', encoding='cp1251', errors='ignore') as f:
                    sys.stdout = f         # Redirect standard output to the file
                    print("* **Имя файла:** `" + filename + "`")                    
                    sys.stdout = original_stdout # Reset standard output to the console
                    
        if attachments != None and isNeedToSaveText == 'y':
            original_stdout = sys.stdout # Save the original stdout
            with open(txtfilename, 'a', encoding='cp1251', errors='ignore') as f:
                sys.stdout = f         # Redirect standard output to the file
                if attchmentLocalCounter == 0:
                    print('Отдельных вложений нет.')
                print('')
                print('')
                sys.stdout = original_stdout # Reset standard output to the console                

    # замена имен файлов вложений в конечном файле
    if isNeedToRenameAttachments == 'y':
        with open (txtfilename, 'r') as f:
            data = f.read()
            
        for key, value in files.items():
            data = data.replace(key, value[1])    

        with open (txtfilename, 'w') as f:
            f.write(data)

        
    print('Всего вложений: ', attachTC)
    print('Скачано вложений: ', TCAttachementsDownloadedCounter)
    
except:
    trace = input('Show trace? y/n ')
    if trace == 'y':
        traceback.print_exc()
