from datetime import date, timedelta
import pytest
from app.models.olympiad import Olympiad
from app.records import insert_olympiad
from app.database import connect
from app.runtime import run

BASE='/api/v1'


def payload(teacher):
    return {'title':'Новая олимпиада','description':'Описание','teacherId':teacher,
            'startDate':date.today().isoformat(),'endDate':date.today().isoformat()}


def test_crud(client, accounts, headers):
    """Карточку можно создать, получить, изменить и удалить."""
    data=payload(accounts['teacher'].id)
    response=client.post(BASE+'/olympiads',json=data,headers=headers['admin'])
    assert response.status_code==201
    oid=response.json()['id']; url=BASE+f'/olympiads/{oid}'
    assert client.get(url).json()['title']==data['title']
    assert client.patch(url,json={'title':'Изменённая олимпиада'},headers=headers['admin']).json()['title']=='Изменённая олимпиада'
    data['description']='Полная замена'
    assert client.put(url,json=data,headers=headers['admin']).json()['description']=='Полная замена'
    assert client.delete(url,headers=headers['admin']).status_code==204
    assert client.get(url).status_code==404


@pytest.mark.parametrize('actor', ['student','teacher'])
def test_crud_forbidden(client, headers, accounts, olympiad, actor):
    """Студент и преподаватель не управляют карточками администратора."""
    header=headers[actor]
    assert client.post(BASE+'/olympiads',json=payload(accounts['teacher'].id),headers=header).status_code==403
    assert client.patch(BASE+f'/olympiads/{olympiad.id}',json={'title':'Новое название'},headers=header).status_code==403
    assert client.delete(BASE+f'/olympiads/{olympiad.id}',headers=header).status_code==403


def test_filter_and_versions(client, db, accounts, olympiad):
    """Отбор, поиск и пагинация возвращают ожидаемые мероприятия."""
    async def add_history():
        async with await connect() as connection:
            await insert_olympiad(connection, Olympiad(title='Историческая олимпиада',
                teacher_id=accounts['teacher'].id, start_date=date(2020,1,1), end_date=date(2020,1,1)))
    run(add_history())
    response=client.get(BASE+'/olympiads',params={'year':2020})
    assert len(response.json())==1
    assert isinstance(client.get(BASE+'/olympiads').json(),list)
    data=client.get('/api/v2/olympiads',params={'pageSize':1}).json()
    assert data['total']==2 and len(data['items'])==1
    assert client.get('/api/v2/olympiads',params={'search':'Python'}).json()['total']==1
    assert client.get('/api/v2/olympiads',params={'search':'%'}).json()['total']==0
    assert client.get('/api/v2/olympiads',params={'page':3,'pageSize':1}).json()['items']==[]
    assert client.get('/api/v2/olympiads',params={'year':2020}).json()['total']==1


@pytest.mark.parametrize('params', [{'page':0},{'pageSize':0},{'pageSize':101},{'year':1999}])
def test_pagination_validation(client,params):
    """Некорректные параметры страницы отклоняются."""
    assert client.get('/api/v2/olympiads',params=params).status_code==422


def test_invalid_olympiad(client, headers, accounts, olympiad):
    """Неверные даты и реквизиты олимпиады дают 422."""
    data=payload(accounts['student'].id)
    assert client.post(BASE+'/olympiads',json=data,headers=headers['admin']).status_code==422
    data=payload(9999999)
    assert client.post(BASE+'/olympiads',json=data,headers=headers['admin']).status_code==422
    data=payload(accounts['teacher'].id); data['endDate']='2000-01-01'
    assert client.post(BASE+'/olympiads',json=data,headers=headers['admin']).status_code==422
    url=BASE+f'/olympiads/{olympiad.id}'
    assert client.patch(url,json={'endDate':'2000-01-01'},headers=headers['admin']).status_code==422
    assert client.patch(url,json={'title':None},headers=headers['admin']).status_code==422
    assert client.patch(url,json={'teacherId':accounts['student'].id},headers=headers['admin']).status_code==422
    assert client.patch(url,json={'teacherId':accounts['other_teacher'].id},headers=headers['admin']).status_code==200


def test_cannot_modify_finalized(client, db, headers, olympiad):
    """Подготовленный протокол блокирует изменение карточки."""
    db.execute("UPDATE olympiads SET protocol_status = 'prepared' WHERE id = %s", (olympiad.id,))
    url=BASE+f'/olympiads/{olympiad.id}'
    assert client.patch(url,json={'title':'Новое название'},headers=headers['admin']).status_code==409
    assert client.delete(url,headers=headers['admin']).status_code==409


def test_inactive_teacher(client, db, accounts, headers):
    """Заблокированного преподавателя нельзя назначить ответственным."""
    db.execute("UPDATE users SET is_active = false WHERE id = %s", (accounts['teacher'].id,))
    assert client.post(BASE+'/olympiads',json=payload(accounts['teacher'].id),headers=headers['admin']).status_code==422
