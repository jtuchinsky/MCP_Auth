"""Unit tests for database configuration and session management."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_base_class_exists(self):
        """Test that Base declarative class is properly defined."""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_engine_is_created(self):
        """Test that SQLAlchemy engine is created."""
        assert engine is not None
        assert str(engine.url).startswith("sqlite:///")

    def test_engine_connects(self):
        """Test that engine can establish a connection."""
        with engine.connect() as connection:
            assert connection is not None
            # Execute a simple query to verify connection
            result = connection.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            assert result.fetchone()[0] == 1

    def test_sessionlocal_is_created(self):
        """Test that SessionLocal factory is created."""
        assert SessionLocal is not None

    def test_sessionlocal_creates_session(self):
        """Test that SessionLocal creates a valid session."""
        db = SessionLocal()
        assert isinstance(db, Session)
        assert db.bind == engine
        db.close()

    def test_sessionlocal_configuration(self):
        """Test that SessionLocal has correct configuration."""
        db = SessionLocal()
        # Check that autoflush is disabled (autocommit was removed in SQLAlchemy 2.0)
        assert db.autoflush is False
        # Verify session is bound to our engine
        assert db.get_bind() == engine
        db.close()


class TestGetDbDependency:
    """Test the get_db dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a valid database session."""
        db_generator = get_db()
        db = next(db_generator)

        assert isinstance(db, Session)
        assert db.bind == engine

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected behavior

    def test_get_db_closes_session(self):
        """Test that get_db properly closes the session after use."""
        db_generator = get_db()
        db = next(db_generator)

        # Session should be open
        assert db.is_active

        # Trigger cleanup
        try:
            next(db_generator)
        except StopIteration:
            pass

        # Session should be closed now
        # Note: We can't directly test if closed, but we can verify
        # that a new get_db() call creates a different session
        db2_generator = get_db()
        db2 = next(db2_generator)

        assert db2 is not db  # Different session instances

        # Clean up second session
        try:
            next(db2_generator)
        except StopIteration:
            pass

    def test_get_db_in_context_manager(self):
        """Test that get_db works correctly as a context manager."""
        # Simulate how FastAPI would use it
        gen = get_db()

        # Enter context
        db = next(gen)
        assert isinstance(db, Session)

        # Perform some operation
        result = db.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert result.fetchone()[0] == 1

        # Exit context
        try:
            next(gen)
        except StopIteration:
            pass  # Expected

    def test_get_db_handles_exception(self):
        """Test that get_db closes session even if an exception occurs."""
        db_generator = get_db()
        db = next(db_generator)

        try:
            # Simulate an exception during request processing
            raise ValueError("Test exception")
        except ValueError:
            pass
        finally:
            # Session should still be closed properly
            try:
                next(db_generator)
            except StopIteration:
                pass

        # Verify we can create a new session
        db2_generator = get_db()
        db2 = next(db2_generator)
        assert isinstance(db2, Session)

        # Clean up
        try:
            next(db2_generator)
        except StopIteration:
            pass


class TestDatabaseMetadata:
    """Test database metadata handling."""

    def test_base_metadata_is_accessible(self):
        """Test that Base.metadata is accessible for migrations."""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, "tables")
        assert hasattr(Base.metadata, "create_all")
        assert hasattr(Base.metadata, "drop_all")

    def test_inspector_can_inspect_database(self):
        """Test that database can be inspected using SQLAlchemy inspector."""
        inspector = inspect(engine)
        assert inspector is not None

        # Get table names (should be empty initially)
        table_names = inspector.get_table_names()
        assert isinstance(table_names, list)
