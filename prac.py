from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_token, verifyToken, hash_password
from database import get_db
from models import User
from schemas import UserSignup, UserOut

@app.post("/auth/signup", response_model=UserOut, status_code=201)
def signup(
    data: UserSignup,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = hash_password(data.password)

    user = User(
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name
    )
-- 1. Diagnostic centres
INSERT INTO diagnostic_centres (name, address, city, is_active)
VALUES
('Apollo Diagnostics', 'MG Road, Connaught Place', 'Delhi', true),
('Max Healthcare Diagnostics', 'Saket', 'Delhi', true),
('Dr Lal PathLabs', 'Sector 18, Noida', 'Noida', true),
('Metropolis Healthcare', 'Andheri West', 'Mumbai', true);


-- 2. Diagnostic tests
INSERT INTO diagnostic_tests (name, description)
VALUES
('CBC', 'Complete Blood Count'),
('Lipid Profile', 'Measures cholesterol and triglyceride levels'),
('Liver Function Test', 'Evaluates liver health and function'),
('Kidney Function Test', 'Evaluates kidney health and function'),
('Blood Sugar', 'Measures blood glucose level'),
('Thyroid Profile', 'Measures thyroid hormone levels');


-- 3. Which centre offers which test + price
INSERT INTO centre_tests (centre_id, test_id, price)
VALUES
-- Apollo Diagnostics
(1, 1, 500.00),
(1, 2, 800.00),
(1, 3, 900.00),
(1, 5, 300.00),
(1, 6, 700.00),

-- Max Healthcare
(2, 1, 550.00),
(2, 2, 850.00),
(2, 4, 950.00),
(2, 5, 350.00),
(2, 6, 750.00),

-- Dr Lal PathLabs
(3, 1, 450.00),
(3, 2, 750.00),
(3, 3, 850.00),
(3, 4, 900.00),
(3, 5, 250.00),

-- Metropolis
(4, 1, 480.00),
(4, 3, 880.00),
(4, 4, 920.00),
(4, 6, 680.00);
    db.add(user)
    db.commit()
    db.refresh(user)

    return user