"""
This module provides refactoring examples for different types of code smells.
Each function returns concrete code examples showing how to refactor the problematic code.
"""

def get_python_refactoring_examples(smell_type, details):
    """Returns concrete refactoring examples for Python code smells."""
    examples = {
        "high_complexity_functions": lambda funcs: {
            "before": """def complex_function(data):
    result = 0
    for item in data:
        if item > 10:
            if isinstance(item, int):
                if item % 2 == 0:
                    result += item * 2
                else:
                    result += item
            else:
                try:
                    num = float(item)
                    result += num
                except:
                    pass
    return result""",
            "after": """def is_valid_number(item):
    return isinstance(item, (int, float)) or str(item).replace('.', '').isdigit()

def process_even_number(num):
    return num * 2 if num % 2 == 0 else num

def process_item(item):
    if not is_valid_number(item) or item <= 10:
        return 0
    try:
        num = float(item) if isinstance(item, str) else item
        return process_even_number(num) if isinstance(num, int) else num
    except ValueError:
        return 0

def refactored_function(data):
    return sum(process_item(item) for item in data)"""
        },

        "deeply_nested_functions": lambda funcs: {
            "before": """def process_data(data):
    results = []
    for item in data:
        if item.is_valid():
            if item.type == 'user':
                if item.age >= 18:
                    if item.has_permission:
                        results.append(item.process())
    return results""",
            "after": """def meets_criteria(item):
    return (item.is_valid() and 
            item.type == 'user' and 
            item.age >= 18 and 
            item.has_permission)

def process_data(data):
    return [item.process() for item in data if meets_criteria(item)]"""
        },

        "feature_envy": lambda funcs: {
            "before": """class Order:
    def __init__(self, customer):
        self.customer = customer
    
    def calculate_discount(self):
        if self.customer.loyalty_years > 5:
            if self.customer.purchase_history > 1000:
                return 0.2
            return 0.1
        return 0""",
            "after": """class Customer:
    def __init__(self, loyalty_years, purchase_history):
        self.loyalty_years = loyalty_years
        self.purchase_history = purchase_history
    
    def calculate_discount(self):
        if self.loyalty_years > 5:
            return 0.2 if self.purchase_history > 1000 else 0.1
        return 0

class Order:
    def __init__(self, customer):
        self.customer = customer
    
    def get_discount(self):
        return self.customer.calculate_discount()"""
        },

        "duplicate_code": lambda funcs: {
            "before": """def process_users(users):
    for user in users:
        name = user.get('name', '').strip()
        email = user.get('email', '').strip()
        if name and '@' in email:
            save_to_db(name, email)

def process_customers(customers):
    for customer in customers:
        name = customer.get('name', '').strip()
        email = customer.get('email', '').strip()
        if name and '@' in email:
            save_to_db(name, email)""",
            "after": """def is_valid_contact(name, email):
    return bool(name.strip() and '@' in email)

def process_contacts(contacts):
    for contact in contacts:
        name = contact.get('name', '').strip()
        email = contact.get('email', '').strip()
        if is_valid_contact(name, email):
            save_to_db(name, email)

def process_users(users):
    process_contacts(users)

def process_customers(customers):
    process_contacts(customers)"""
        },

        "too_many_returns": lambda funcs: {
            "before": """def check_user_access(user):
    if not user:
        return False
    if not user.is_active:
        return False
    if user.is_banned:
        return False
    if not user.has_permission('access'):
        return False
    if user.login_attempts > 3:
        return False
    return True""",
            "after": """def check_user_access(user):
    conditions = [
        bool(user),
        user.is_active,
        not user.is_banned,
        user.has_permission('access'),
        user.login_attempts <= 3
    ]
    return all(conditions)"""
        }
    }
    
    return examples.get(smell_type, lambda x: {"before": "No example available", "after": "No example available"})(details)

def get_javascript_refactoring_examples(smell):
    """Returns concrete refactoring examples for JavaScript code smells."""
    parts = smell.split(":")
    smell_type = parts[0].strip()
    
    examples = {
        "Global Variables Found": {
            "before": """// script.js
var users = [];
var config = { apiUrl: 'https://api.example.com' };

function addUser(user) {
    users.push(user);
}

function getConfig() {
    return config;
}""",
            "after": """// users.js
export class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
    }
}

// config.js
export const config = {
    apiUrl: 'https://api.example.com'
};

// main.js
import { UserManager } from './users';
import { config } from './config';

const userManager = new UserManager();"""
        },

        "Unused Variables": {
            "before": """function processData(data) {
    let temp = data.map(x => x * 2);  // Unused variable
    let result = data.filter(x => x > 10);
    return result;
}""",
            "after": """function processData(data) {
    // Remove unused variable and directly return filtered result
    return data.filter(x => x > 10);
}"""
        },

        "Deep Nesting": {
            "before": """function processUserData(user) {
    if (user) {
        if (user.address) {
            if (user.address.shipping) {
                if (user.address.shipping.zipCode) {
                    return validateZipCode(user.address.shipping.zipCode);
                }
            }
        }
    }
    return false;
}""",
            "after": """function processUserData(user) {
    if (!user?.address?.shipping?.zipCode) {
        return false;
    }
    return validateZipCode(user.address.shipping.zipCode);
}"""
        },

        "Magic Numbers Found": {
            "before": """function calculatePrice(quantity) {
    if (quantity > 10) {
        return quantity * 5.99 * 0.9;
    }
    return quantity * 5.99;
}

setTimeout(checkStatus, 300000);""",
            "after": """const PRICES = {
    UNIT_PRICE: 5.99,
    BULK_DISCOUNT: 0.9,
    BULK_THRESHOLD: 10
};

const TIMEOUTS = {
    STATUS_CHECK: 5 * 60 * 1000 // 5 minutes in milliseconds
};

function calculatePrice(quantity) {
    const basePrice = quantity * PRICES.UNIT_PRICE;
    return quantity > PRICES.BULK_THRESHOLD 
        ? basePrice * PRICES.BULK_DISCOUNT 
        : basePrice;
}

setTimeout(checkStatus, TIMEOUTS.STATUS_CHECK);"""
        },

        "Callback Hell": {
            "before": """getData(function(a) {
    getMoreData(a, function(b) {
        getMoreData(b, function(c) {
            getMoreData(c, function(d) {
                getMoreData(d, function(e) {
                    console.log(e);
                });
            });
        });
    });
});""",
            "after": """// Using async/await
async function getAllData() {
    try {
        const a = await getData();
        const b = await getMoreData(a);
        const c = await getMoreData(b);
        const d = await getMoreData(c);
        const e = await getMoreData(d);
        return e;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
}

// Or using Promise chaining
getData()
    .then(a => getMoreData(a))
    .then(b => getMoreData(b))
    .then(c => getMoreData(c))
    .then(d => getMoreData(d))
    .then(e => console.log(e))
    .catch(error => console.error('Error:', error));"""
        },

        "Duplicate Code Blocks": {
            "before": """function validateUser(user) {
    if (!user.name || user.name.length < 2) {
        throw new Error('Invalid name');
    }
    if (!user.email || !user.email.includes('@')) {
        throw new Error('Invalid email');
    }
    return true;
}

function validateCustomer(customer) {
    if (!customer.name || customer.name.length < 2) {
        throw new Error('Invalid name');
    }
    if (!customer.email || !customer.email.includes('@')) {
        throw new Error('Invalid email');
    }
    return true;
}""",
            "after": """const validations = {
    name: (name) => {
        if (!name || name.length < 2) {
            throw new Error('Invalid name');
        }
    },
    email: (email) => {
        if (!email || !email.includes('@')) {
            throw new Error('Invalid email');
        }
    }
};

function validateContact(contact) {
    validations.name(contact.name);
    validations.email(contact.email);
    return true;
}

const validateUser = validateContact;
const validateCustomer = validateContact;"""
        }
    }
    
    return examples.get(smell_type, {
        "before": "No example available",
        "after": "No example available"
    })

