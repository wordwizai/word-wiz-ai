import random
import string
from sqlalchemy.orm import Session as orm_session
from sqlalchemy.orm import selectinload
from models.class_model import Class
from typing import List, Optional


def generate_unique_join_code(db: orm_session, length: int = 6) -> str:
    """Generate a unique join code for a class.
    
    Args:
        db: Database session
        length: Length of the join code (default: 6)
        
    Returns:
        A unique join code string
    """
    # Use only unambiguous characters (avoid 0/O, 1/I/l)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    
    # Try up to 10 times to generate a unique code
    for _ in range(10):
        code = ''.join(random.choices(chars, k=length))
        existing = db.query(Class).filter(Class.join_code == code).first()
        if not existing:
            return code
    
    # If we couldn't generate a unique code in 10 tries, increase length
    return generate_unique_join_code(db, length + 1)


def create_class(db: orm_session, name: str, teacher_id: int) -> Class:
    """Create a new class.
    
    Args:
        db: Database session
        name: Name of the class
        teacher_id: ID of the teacher creating the class
        
    Returns:
        The created Class object
    """
    join_code = generate_unique_join_code(db)
    db_class = Class(
        name=name,
        join_code=join_code,
        teacher_id=teacher_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


def get_class_by_id(db: orm_session, class_id: int) -> Optional[Class]:
    """Get a class by its ID.
    
    Args:
        db: Database session
        class_id: ID of the class
        
    Returns:
        The Class object or None if not found
    """
    return db.query(Class).filter(Class.id == class_id).first()


def get_class_by_join_code(db: orm_session, join_code: str) -> Optional[Class]:
    """Get a class by its join code.
    
    Args:
        db: Database session
        join_code: Join code of the class
        
    Returns:
        The Class object or None if not found
    """
    return db.query(Class).filter(Class.join_code == join_code.upper()).first()


def get_teacher_classes(db: orm_session, teacher_id: int) -> List[Class]:
    """Get all classes created by a teacher.
    
    Args:
        db: Database session
        teacher_id: ID of the teacher
        
    Returns:
        List of Class objects
    """
    return (
        db.query(Class)
        .options(selectinload(Class.memberships))
        .filter(Class.teacher_id == teacher_id)
        .order_by(Class.created_at.desc())
        .all()
    )


def delete_class(db: orm_session, class_id: int) -> bool:
    """Delete a class.
    
    Args:
        db: Database session
        class_id: ID of the class to delete
        
    Returns:
        True if deleted, False if not found
    """
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if db_class:
        db.delete(db_class)
        db.commit()
        return True
    return False
