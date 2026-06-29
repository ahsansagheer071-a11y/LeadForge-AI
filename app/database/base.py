from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class.
    Automatically generates table names from class names (converted to lowercase plural/singular).
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase class name to snake_case table name
        name = cls.__name__
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        
        # Pluralize simple names, e.g. User -> users, Lead -> leads
        table_name = "".join(result)
        if table_name.endswith('y'):
            return f"{table_name[:-1]}ies"
        elif not table_name.endswith('s'):
            return f"{table_name}s"
        return table_name


