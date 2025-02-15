import pytest
from app import app, db
from models import Contact

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    # Create test client
    with app.test_client() as client:
        with app.app_context():
            # Create all tables in the test database
            db.create_all()
            yield client
            # Clean up after tests
            db.session.remove()
            db.drop_all()

@pytest.fixture
def sample_contact():
    contact = Contact(
        name='John Doe',
        phone='1234567890',
        email='john@example.com',
        type='Personal'
    )
    db.session.add(contact)
    db.session.commit()
    return contact

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_add_contact(client):
    data = {
        'name': 'Jane Doe',
        'phone': '9876543210',
        'email': 'jane@example.com',
        'type': 'Personal'
    }
    response = client.post('/add', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Jane Doe' in response.data

def test_update_contact(client, sample_contact):
    data = {
        'name': 'John Smith',
        'phone': sample_contact.phone,
        'email': sample_contact.email,
        'type': sample_contact.type,
        'submit': 'Update'
    }
    response = client.post(
        f'/update/{sample_contact.id}',
        data=data,
        follow_redirects= True
    )
    assert response.status_code == 200
    updated_contact = db.session.get(Contact, sample_contact.id)
    assert updated_contact.name == 'John Smith'


def test_delete_contact(client, sample_contact):
    # Ensure the contact exists before deletion
    assert db.session.get(Contact, sample_contact.id) is not None

    # Send DELETE request to delete the contact
    response = client.post(f'/delete/{sample_contact.id}', follow_redirects=True)
    assert response.status_code == 200

    # Ensure the contact was deleted
    deleted_contact = db.session.get(Contact, sample_contact.id)
    assert deleted_contact is None

def test_view_contact(client, sample_contact):
    # Send a GET request to view the contact details
    response = client.get(f'/contact/{sample_contact.id}')
    assert response.status_code == 200

    # Ensure the contact's details are displayed correctly
    assert b'John Doe' in response.data
    assert b'1234567890' in response.data
    assert b'john@example.com' in response.data
    assert b'Personal' in response.data


def test_get_contacts_api(client, sample_contact):
    response = client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'John Doe'

def test_get_single_contact_api(client, sample_contact):
    response = client.get(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'John Doe'

def test_create_contact_api(client):
    data = {
        'name': 'API User',
        'phone': '5555555555',
        'email': 'api@example.com',
        'type': 'work'
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 201
    assert response.get_json()['name'] == 'API User'

def test_update_contact_api(client, sample_contact):
    updated_data = {
        'name': 'John Updated',
        'phone': '5551234567',
        'email': 'john.updated@example.com',
        'type': 'personal'
    }
    response = client.put(f'/api/contacts/{sample_contact.id}', json=updated_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'John Updated'
    assert data['phone'] == '5551234567'
    assert data['email'] == 'john.updated@example.com'
    assert data['type'] == 'personal'


def test_delete_contact_api(client, sample_contact):
    response = client.delete(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 204

    # Confirm the contact has been deleted by trying to get it again
    response = client.get(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 404


def test_list_contact_api(client, sample_contact):
    response = client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    # Check if the sample_contact is in the list of contacts
    assert any(contact['id'] == sample_contact.id for contact in data)


# Test error cases
def test_invalid_contact_creation(client):
    data = {
        'name': 'Invalid User',
        # Missing required fields
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 400

def test_get_nonexistent_contact(client):
    response = client.get('/api/contacts/999')
    assert response.status_code == 404  