"""
Service Layer Unit Tests

Tests for AI analyzer, authentication services, and configuration.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAIAnalyzerRuleBased:
    """Tests for AI analyzer rule-based intent matching."""

    @pytest.mark.asyncio
    async def test_rule_based_cnv(self):
        """Test CNV intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        # Mock API key to force rule-based mode
        analyzer.api_key = None

        result = await analyzer.analyze_intent("I need to do CNV analysis")
        assert result["category"] == "cnv"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_differential_expression(self):
        """Test differential expression intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Run differential expression analysis with edgeR")
        assert result["category"] == "de"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_qc(self):
        """Test quality control intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("I need quality control for my samples")
        assert result["category"] == "qc"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_rnaseq(self):
        """Test RNA-seq intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Analyze my RNA-seq data using STAR")
        assert result["category"] == "rnaseq"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_wgs(self):
        """Test WGS variant calling intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Run WGS variant calling with GATK")
        assert result["category"] == "wgs"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_metagenomics(self):
        """Test metagenomics intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Analyze metagenomics data with Kraken2")
        assert result["category"] == "metagenomics"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_rule_based_single_cell(self):
        """Test single-cell RNA-seq intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Analyze single-cell RNA-seq data")
        assert result["category"] == "single_cell"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_rule_based_unknown(self):
        """Test unknown intent detection."""
        from services.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        analyzer.api_key = None

        result = await analyzer.analyze_intent("Hello world")
        assert result["category"] == "unknown"
        assert result["confidence"] == 0.3


class TestAuthService:
    """Tests for authentication service functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from services.auth import get_password_hash, verify_password

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_token_creation_and_decode(self):
        """Test JWT token creation and decoding."""
        from services.auth import create_access_token, decode_access_token

        data = {"sub": "testuser", "roles": ["admin"]}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        decoded = decode_access_token(token)
        assert decoded == "testuser"

    def test_token_decode_invalid(self):
        """Test decoding invalid token."""
        from services.auth import decode_access_token

        decoded = decode_access_token("invalid.token.here")
        assert decoded is None


class TestConfig:
    """Tests for configuration loading."""

    def test_settings_loading(self):
        """Test that settings can be loaded."""
        from config import get_settings

        settings = get_settings()
        assert settings is not None
        assert settings.app_name == "OmicsFlow Backend"
        assert settings.debug is True

    def test_settings_defaults(self):
        """Test default settings values."""
        from config import Settings

        settings = Settings()
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30

    def test_settings_from_env(self):
        """Test settings can be loaded from environment."""
        import os
        # Temporarily set environment variable
        original_value = os.environ.get("APP_NAME")
        try:
            os.environ["APP_NAME"] = "Test App"
            # Clear cache to allow re-reading
            from config import get_settings
            get_settings.cache_clear()

            settings = get_settings()
            assert settings.app_name == "Test App"
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop("APP_NAME", None)
            else:
                os.environ["APP_NAME"] = original_value
            get_settings.cache_clear()
