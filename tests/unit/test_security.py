"""Unit tests for password hashing and verification."""

import pytest

from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_produces_bcrypt_hash(self):
        """Test that hash_password produces a bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ (or $2a$/$2y$)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_password_uses_correct_cost_factor(self):
        """Test that hash_password uses cost factor 12."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Bcrypt hash format: $2b$12$... where 12 is the cost factor
        # Extract cost factor from hash (characters 4-6)
        cost_factor = hashed[4:6]
        assert cost_factor == "12"

    def test_hash_password_different_for_same_input(self):
        """Test that hash_password produces different hashes (due to salt)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Same password should produce different hashes (bcrypt uses random salt)
        assert hash1 != hash2

    def test_hash_password_different_for_different_inputs(self):
        """Test that different passwords produce different hashes."""
        password1 = "password_one"
        password2 = "password_two"

        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        assert hash1 != hash2

    def test_hash_password_handles_special_characters(self):
        """Test that hash_password handles special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_handles_unicode(self):
        """Test that hash_password handles unicode characters."""
        password = "пароль密码🔒"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_handles_empty_string(self):
        """Test that hash_password handles empty string."""
        password = ""
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestPasswordVerification:
    """Test password verification functionality."""

    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(correct_password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that verify_password is case-sensitive."""
        password = "Password123"
        hashed = hash_password(password)

        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False
        assert verify_password("Password123", hashed) is True

    def test_verify_password_with_special_characters(self):
        """Test password verification with special characters."""
        password = "p@ssw0rd!#$"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("p@ssw0rd!#", hashed) is False

    def test_verify_password_with_unicode(self):
        """Test password verification with unicode characters."""
        password = "пароль密码🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_empty_string(self):
        """Test password verification with empty string."""
        password = ""
        hashed = hash_password(password)

        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_verify_password_with_whitespace(self):
        """Test that verify_password preserves whitespace."""
        password = "password with spaces"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("passwordwithspaces", hashed) is False
        assert verify_password(" password with spaces", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """Test that verify_password raises exception for invalid hash format."""
        from passlib.exc import UnknownHashError

        password = "test_password"
        invalid_hash = "not_a_valid_bcrypt_hash"

        # Passlib should raise UnknownHashError for invalid hash format
        with pytest.raises(UnknownHashError):
            verify_password(password, invalid_hash)


class TestPasswordHashingIntegration:
    """Integration tests for password hashing and verification."""

    def test_hash_and_verify_workflow(self):
        """Test complete hash and verify workflow."""
        # User registration
        user_password = "new_user_password_123"
        stored_hash = hash_password(user_password)

        # User login with correct password
        login_attempt_1 = "new_user_password_123"
        assert verify_password(login_attempt_1, stored_hash) is True

        # User login with incorrect password
        login_attempt_2 = "wrong_password"
        assert verify_password(login_attempt_2, stored_hash) is False

    def test_multiple_users_different_hashes(self):
        """Test that multiple users with same password get different hashes."""
        same_password = "common_password"

        user1_hash = hash_password(same_password)
        user2_hash = hash_password(same_password)
        user3_hash = hash_password(same_password)

        # All hashes should be different (due to random salts)
        assert user1_hash != user2_hash
        assert user2_hash != user3_hash
        assert user1_hash != user3_hash

        # But all should verify correctly
        assert verify_password(same_password, user1_hash) is True
        assert verify_password(same_password, user2_hash) is True
        assert verify_password(same_password, user3_hash) is True

    def test_password_change_workflow(self):
        """Test password change workflow."""
        # Original password
        old_password = "old_password_123"
        old_hash = hash_password(old_password)

        # Verify old password works
        assert verify_password(old_password, old_hash) is True

        # User changes password
        new_password = "new_password_456"
        new_hash = hash_password(new_password)

        # Old password should not work with new hash
        assert verify_password(old_password, new_hash) is False

        # New password should work with new hash
        assert verify_password(new_password, new_hash) is True

        # New password should not work with old hash
        assert verify_password(new_password, old_hash) is False
