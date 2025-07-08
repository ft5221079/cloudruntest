import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. 配置参数
FOLDER_ID = "1Lbf88mc4vAWCklDszhACLiauvA4CH4q6"
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]

# 2. 获取 Google API 服务
def get_service(api_name, version):
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )
    return build(api_name, version, credentials=credentials)

# 3. 递归获取文件夹内所有文件信息
def list_files_recursive(service, folder_id, parent_path=""):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, pageSize=1000, fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])
    for item in items:
        path = f"{parent_path}/{item['name']}"
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            yield from list_files_recursive(service, item['id'], path)
        else:
            yield {
                "id": item['id'],
                "name": item['name'],
                "path": path,
                "mimeType": item['mimeType'],
            }

# 4. 新建 Google Sheet 并写入数据
def write_to_sheet(sheets_service, data):
    # 创建新的表格
    spreadsheet = sheets_service.spreadsheets().create(
        body={
            'properties': {'title': 'Drive Files Export'}
        },
        fields='spreadsheetId'
    ).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    # 构造表头和内容
    header = ["ID", "文件名", "完整路径", "类型"]
    values = [header] + [
        [item['id'], item['name'], item['path'], item['mimeType']] for item in data
    ]
    # 写入内容
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()
    print("数据已写入 Google Sheet：", f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    return spreadsheet_id

def main():
    # 初始化服务
    drive_service = get_service('drive', 'v3')
    sheets_service = get_service('sheets', 'v4')
    # 获取所有文件信息
    files = list(list_files_recursive(drive_service, FOLDER_ID))
    print(f"共获取到{len(files)}个文件")
    # 新建表格并写入
    spreadsheet_id = write_to_sheet(sheets_service, files)

if __name__ == "__main__":
    main()
