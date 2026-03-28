import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.models import Client

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate 100 random clients'

    first_names = [
        'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
        'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
        'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Lisa', 'Daniel', 'Nancy',
        'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
        'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
        'Kenneth', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa',
        'Timothy', 'Deborah', 'Ronald', 'Stephanie', 'Edward', 'Rebecca', 'Jason', 'Sharon',
        'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
        'Nicholas', 'Angela', 'Eric', 'Shirley', 'Jonathan', 'Anna', 'Stephen', 'Brenda',
        'Larry', 'Pamela', 'Justin', 'Emma', 'Scott', 'Nicole', 'Brandon', 'Helen',
    ]

    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
        'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
        'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
        'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
        'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
        'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
    ]

    company_suffixes = [
        'LLC', 'Inc', 'Corp', 'Ltd', 'Group', 'Solutions', 'Services', 'Systems',
        'Technologies', 'Industries', 'Partners', 'Associates', 'Enterprise', 'Company',
    ]

    cities = [
        'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
        'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
        'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle',
        'Denver', 'Boston', 'Portland', 'Las Vegas', 'Detroit', 'Nashville', 'Memphis',
        'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno',
        'Sacramento', 'Kansas City', 'Miami', 'Atlanta', 'Cleveland', 'Minneapolis',
    ]

    streets = [
        'Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Park Blvd', 'Washington St',
        'Highland Ave', 'Lake Rd', 'Sunset Dr', 'Church St', 'Mill Rd', 'Center St',
        'School St', 'Garden Ave', 'Spring St', 'River Rd', 'Hill St', 'Walnut St',
        'Broadway', 'Madison Ave', 'Lincoln Ave', 'Jefferson St', 'Crown Ct', 'Valley View',
    ]

    def generate_email(self, first_name, last_name, company_name=None):
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'email.com']
        if company_name and random.random() > 0.3:
            domain = company_name.lower().replace(' ', '').replace('.', '') + '.com'
        else:
            domain = random.choice(domains)
        return f'{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{domain}'

    def generate_phone(self):
        return f'+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}'

    def generate_address(self):
        street_num = random.randint(1, 9999)
        street = random.choice(self.streets)
        return f'{street_num} {street}'

    def generate_company_code(self):
        return f'{random.randint(100000000, 999999999)}'

    def generate_vat_code(self):
        return f'GB{random.randint(100000000, 999999999)}'

    def handle(self, *args, **options):
        # Get the first user or create one if needed
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        clients = []
        for i in range(100):
            client_type = random.choice([Client.CLIENT_BUSINESS, Client.CLIENT_INDIVIDUAL])
            
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            
            if client_type == Client.CLIENT_BUSINESS:
                company_suffix = random.choice(self.company_suffixes)
                name = f'{last_name} {company_suffix}'
                company_code = self.generate_company_code()
                vat_code = self.generate_vat_code() if random.random() > 0.3 else ''
            else:
                name = f'{first_name} {last_name}'
                company_code = ''
                vat_code = ''

            email = self.generate_email(first_name, last_name, name if client_type == Client.CLIENT_BUSINESS else None)
            phone_number = self.generate_phone() if random.random() > 0.2 else ''
            address = self.generate_address() if random.random() > 0.2 else ''
            city = random.choice(self.cities) if random.random() > 0.2 else ''

            client = Client(
                user=user,
                client_type=client_type,
                name=name,
                company_code=company_code,
                vat_code=vat_code,
                email=email,
                phone_number=phone_number,
                address=address,
                city=city,
            )
            clients.append(client)

        Client.objects.bulk_create(clients)
        self.stdout.write(self.style.SUCCESS(f'Successfully created 100 clients for user: {user.email}'))
