import pytest


@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_documentation_and_security_schema(client, version):
    response=client.get(f'/api/{version}/openapi.json')
    assert response.status_code==200
    schema=response.json()
    assert schema['components']['securitySchemes']['OAuth2PasswordBearer']['flows']['password']['tokenUrl']=='auth/token'
    assert schema['paths']['/users']['post']['security']
    for path in ('docs','redoc'):
        response=client.get(f'/api/{version}/{path}')
        assert response.status_code==200
        assert '/static/' in response.text
    result_schema=schema['paths']['/olympiads']['get']['responses']['200']['content']['application/json']['schema']
    assert (result_schema.get('type')=='array') if version=='v1' else ('$ref' in result_schema)


def test_health_and_static(client):
    assert client.get('/health').json()=={'status':'ok','database':'postgresql'}
    assert client.get('/static/swagger-ui.css').status_code==200


@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_complete_response_contracts(client, version):
    schema = client.get(f'/api/{version}/openapi.json').json()
    for operations in schema['paths'].values():
        for operation in operations.values():
            responses = operation['responses']
            for code in ('200', '201'):
                if code not in responses:
                    continue
                content = responses[code]['content']
                if 'application/json' in content:
                    body = content['application/json']['schema']
                    assert '$ref' in body or (body.get('type') == 'array' and '$ref' in body['items'])
                else:
                    assert all(v['schema']['format'] == 'binary' for v in content.values())
            assert responses['401']['content']['application/json']['schema']['$ref'].endswith('/ErrorRead')
    fields = schema['components']['schemas']['ParticipationRead']['properties']
    assert set(fields) == {'id', 'olympiadId', 'studentId', 'fullName', 'score', 'result'}
    assert 'access_token' in schema['components']['schemas']['TokenRead']['properties']

