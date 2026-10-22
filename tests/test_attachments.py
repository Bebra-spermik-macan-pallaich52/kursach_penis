from datetime import date
from io import BytesIO
from docx import Document
from openpyxl import Workbook
import pytest
from app.models import Attachment

BASE='/api/v1'


def upload(client,headers,olympiad,kind='regulation',filename='rules.txt',content=b'Test document'):
    return client.post(BASE+f'/olympiads/{olympiad.id}/attachments',headers=headers['teacher'],
        data={'kind':kind,'title':'Документ олимпиады'},files={'file':(filename,content)})


def test_upload_download_delete(client,headers,olympiad):
    response=upload(client,headers,olympiad); assert response.status_code==201
    fid=response.json()['id']; url=BASE+f'/attachments/{fid}'
    response=client.get(url); assert response.content==b'Test document'
    assert response.headers['x-content-type-options']=='nosniff'
    files=client.get(BASE+f'/olympiads/{olympiad.id}/attachments').json()
    assert len(files)==1 and 'stored_name' not in files[0]
    assert len(client.get(BASE+f'/olympiads/{olympiad.id}/attachments/manage',headers=headers['teacher']).json())==1
    assert client.delete(url,headers=headers['teacher']).status_code==204
    assert client.get(url).status_code==404


def test_past_tasks(client,db,headers,olympiad):
    response=upload(client,headers,olympiad,kind='task'); assert response.status_code==201
    fid=response.json()['id']
    assert client.get(BASE+f'/attachments/{fid}').status_code==404
    assert client.get(BASE+f'/olympiads/{olympiad.id}/attachments').json()==[]
    olympiad.start_date=date(date.today().year-1,1,1)
    olympiad.end_date=olympiad.start_date; db.commit()
    assert client.get(BASE+f'/attachments/{fid}').status_code==200
    assert len(client.get(BASE+f'/olympiads/{olympiad.id}/attachments').json())==1


def test_multiple_awards_and_permissions(client,headers,olympiad):
    r1=upload(client,headers,olympiad,kind='award'); r2=upload(client,headers,olympiad,kind='award')
    assert r1.status_code==r2.status_code==201
    assert len(client.get(BASE+f'/olympiads/{olympiad.id}/attachments').json())==2
    fid=r1.json()['id']; other=headers['other_teacher']
    assert client.delete(BASE+f'/attachments/{fid}',headers=other).status_code==403
    assert client.get(BASE+f'/olympiads/{olympiad.id}/attachments/manage',headers=other).status_code==403
    assert client.post(BASE+f'/olympiads/{olympiad.id}/attachments',headers=other,
        data={'kind':'award','title':'Грамота'},files={'file':('new.txt',b'Test')}).status_code==403
    assert client.delete(BASE+f'/olympiads/{olympiad.id}',headers=headers['admin']).status_code==409


@pytest.mark.parametrize('name,content,kind,status', [
    ('bad.exe',b'executable','regulation',422),('empty.txt',b'','regulation',422),
    ('bad.pdf',b'not pdf','regulation',422),('bad.png',b'not png','award',422),
    ('bad.jpg',b'not jpeg','award',422),('bad.docx',b'not zip','award',422),
    ('bad.txt',b'\xff\xfe','regulation',422),('test.txt',b'OK','unknown',422),
    ('a'*201+'.txt',b'Test','award',422),('large.txt',b'a'*(5*1024*1024+1),'award',413)],
    ids=['extension','empty','fake-pdf','fake-png','fake-jpg','fake-docx','encoding','kind','filename','size'])
def test_file_validation(client,headers,olympiad,name,content,kind,status):
    assert upload(client,headers,olympiad,kind,name,content).status_code==status


@pytest.mark.parametrize('format',['docx','xlsx'])
def test_office_uploads(client,headers,olympiad,format):
    stream=BytesIO()
    if format=='docx': Document().save(stream)
    else: Workbook().save(stream)
    assert upload(client,headers,olympiad,filename='document.'+format,content=stream.getvalue()).status_code==201


def test_missing_file(client,db,headers,olympiad,tmp_path):
    response=upload(client,headers,olympiad); fid=response.json()['id']
    item=db.get(Attachment,fid); (tmp_path/item.stored_name).unlink()
    assert client.get(BASE+f'/attachments/{fid}').status_code==404
    assert client.delete(BASE+'/attachments/99999999',headers=headers['teacher']).status_code==404


def test_no_path_traversal(client,db,headers,olympiad,tmp_path):
    response=upload(client,headers,olympiad,filename='../../escape.txt')
    assert response.status_code==201
    item=db.get(Attachment,response.json()['id'])
    assert item.original_name=='escape.txt'
    assert '/' not in item.stored_name
    assert (tmp_path/item.stored_name).is_file()
