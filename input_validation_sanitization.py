#!/usr/bin/env python3
"""
Input Validation and Sanitization System
AI Agent Review Security Implementation

Critical Security Improvement based on AI Agent Recommendations:
"Add input validation and sanitization" (1 AI model mention, HIGH PRIORITY)

This module provides comprehensive input validation and sanitization
for the DirectAPI system to prevent security vulnerabilities.

Security Features:
✅ Input validation for all data types
✅ XSS prevention
✅ SQL injection prevention
✅ Path traversal protection
✅ Command injection prevention
✅ Data type validation and sanitization
✅ Comprehensive logging of security events
"""

import re
import html
import json
import logging
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import secrets
from datetime import datetime

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ThreatType(Enum):
    """Types of security threats detected"""
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    CODE_INJECTION = "code_injection"
    LDAP_INJECTION = "ldap_injection"
    XXE = "xxe"
    SSRF = "ssrf"

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_value: Any
    threats_detected: List[ThreatType] = field(default_factory=list)
    validation_messages: List[str] = field(default_factory=list)
    original_value: Any = None
    validation_time: float = 0.0
    checksum: str = ""

@dataclass
class SecurityEvent:
    """Security event for logging and monitoring"""
    timestamp: datetime
    threat_type: ThreatType
    severity: ValidationLevel
    input_value: str
    description: str
    source: str = "unknown"
    blocked: bool = True
    additional_data: Dict[str, Any] = field(default_factory=dict)

class InputValidator:
    """
    Comprehensive input validation and sanitization system

    Implements AI agent security recommendation:
    "Add input validation and sanitization"

    Capabilities:
    ✅ XSS attack detection and prevention
    ✅ SQL injection detection and prevention
    ✅ Path traversal attack detection
    ✅ Command injection detection
    ✅ Data type validation and sanitization
    ✅ Comprehensive security logging
    """

    def __init__(self):
        self.logger = logging.getLogger("InputValidator")
        self.security_events: List[SecurityEvent] = []
        self._setup_logging()
        self._initialize_patterns()

    def _setup_logging(self):
        """Setup security-focused logging"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [SECURITY] %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _initialize_patterns(self):
        """Initialize security threat detection patterns"""

        # XSS Detection Patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'alert\s*\(',
            r'confirm\s*\(',
            r'prompt\s*\(',
            r'document\.',
            r'window\.',
            r'location\.',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<style[^>]*>.*?</style>',
        ]

        # SQL Injection Patterns
        self.sql_injection_patterns = [
            r'(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
            r"('|\").*?(\b(OR|AND)\b\s+.*?=.*?)",
            r"(\b(OR|AND)\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(;\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)\b)",
            r"(INFORMATION_SCHEMA|SYS|MASTER|MSDB)",
            r"(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)",
            r"(BENCHMARK|SLEEP|WAITFOR|DELAY)",
            r"(\b(CONCAT|CHAR|ASCII|ORD|HEX)\s*\()",
        ]

        # Path Traversal Patterns
        self.path_traversal_patterns = [
            r'\.\./',
            r'\.\\',
            r'(\w+:)?//',
            r'/etc/',
            r'/proc/',
            r'/sys/',
            r'/%2e%2e/',
            r'/%2e\\',
            r'\\\.\\',
            r'\.\.%2f',
            r'%2f\.\.',
            r'[cC]:\\.*\\[wW]indows',
            r'[cC]:\\.*\\[sS]ystem32',
        ]

        # Command Injection Patterns
        self.command_injection_patterns = [
            r'[;&|`$()]',
            r'\$\(',
            r'`[^`]*`',
            r'\|\|',
            r'&&',
            r';\s*\w+',
            r'>\s*/dev/',
            r'curl\s+',
            r'wget\s+',
            r'nc\s+',
            r'netcat\s+',
            r'bash\s+-',
            r'sh\s+-',
            r'python\s+-',
            r'perl\s+-',
            r'ruby\s+-',
            r'php\s+-',
            r'eval\s+',
            r'exec\s+',
            r'system\s+',
            r'passthru\s+',
        ]

        # Code Injection Patterns
        self.code_injection_patterns = [
            r'<\?php',
            r'<%',
            r'<%',
            r'<\?=',
            r'<script[^>]*runat="server"[^>]*>',
            r'include\s*\(',
            r'require\s*\(',
            r'include_once\s*\(',
            r'require_once\s*\(',
            r'file_get_contents\s*\(',
            r'file_put_contents\s*\(',
            r'fopen\s*\(',
            r'unlink\s*\('',
            r'rmdir\s*\(',
            r'mkdir\s*\(',
            r'chmod\s*\(',
        ]

        # Compile all patterns for performance
        self.compiled_patterns = {
            ThreatType.XSS: [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.xss_patterns],
            ThreatType.SQL_INJECTION: [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.sql_injection_patterns],
            ThreatType.PATH_TRAVERSAL: [re.compile(p, re.IGNORECASE) for p in self.path_traversal_patterns],
            ThreatType.COMMAND_INJECTION: [re.compile(p, re.IGNORECASE) for p in self.command_injection_patterns],
            ThreatType.CODE_INJECTION: [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.code_injection_patterns],
        }

    def validate_string(self, input_value: str, max_length: int = 1000,
                        allow_html: bool = False, source: str = "unknown") -> ValidationResult:
        """
        Validate string input against security threats

        Args:
            input_value: String input to validate
            max_length: Maximum allowed length
            allow_html: Whether HTML content is allowed
            source: Source of the input for logging

        Returns:
            ValidationResult with sanitized output and threat information
        """
        start_time = datetime.now()

        # Initialize result
        result = ValidationResult(
            is_valid=True,
            sanitized_value=input_value,
            original_value=input_value,
            checksum=self._calculate_checksum(input_value)
        )

        # Basic checks
        if not isinstance(input_value, str):
            result.is_valid = False
            result.validation_messages.append(f"Expected string, got {type(input_value).__name__}")
            return result

        if len(input_value) > max_length:
            result.is_valid = False
            result.validation_messages.append(f"Input too long: {len(input_value)} > {max_length}")
            self._log_security_event(
                ThreatType.XSS, ValidationLevel.WARNING, input_value[:100],
                f"Input length exceeded: {len(input_value)} > {max_length}", source, blocked=False
            )

        # Check for security threats
        sanitized_value = input_value
        for threat_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(input_value)
                if matches:
                    result.threats_detected.append(threat_type)
                    result.is_valid = False
                    result.validation_messages.append(f"Security threat detected: {threat_type.value}")

                    # Log security event
                    self._log_security_event(
                        threat_type, ValidationLevel.ERROR, input_value[:100],
                        f"Threat pattern detected: {threat_type.value}", source
                    )

        # Sanitize input
        if not allow_html:
            sanitized_value = self._sanitize_html(sanitized_value)

        sanitized_value = self._sanitize_special_chars(sanitized_value)

        # Update result
        result.sanitized_value = sanitized_value
        result.validation_time = (datetime.now() - start_time).total_seconds()

        # Log validation result
        if result.is_valid:
            self.logger.debug(f"✅ Input validated successfully: {source}")
        else:
            self.logger.warning(f"⚠️ Input validation failed: {source} - {result.validation_messages}")

        return result

    def validate_dict(self, input_dict: Dict[str, Any],
                     allowed_keys: Optional[List[str]] = None,
                     max_key_length: int = 100, max_value_length: int = 1000,
                     source: str = "unknown") -> ValidationResult:
        """
        Validate dictionary input recursively

        Args:
            input_dict: Dictionary to validate
            allowed_keys: List of allowed keys (None allows all)
            max_key_length: Maximum key length
            max_value_length: Maximum value length for strings
            source: Source of the input

        Returns:
            ValidationResult with sanitized dictionary
        """
        start_time = datetime.now()

        result = ValidationResult(
            is_valid=True,
            sanitized_value={},
            original_value=input_dict.copy(),
            checksum=self._calculate_checksum(str(input_dict))
        )

        if not isinstance(input_dict, dict):
            result.is_valid = False
            result.validation_messages.append(f"Expected dict, got {type(input_dict).__name__}")
            return result

        sanitized_dict = {}

        for key, value in input_dict.items():
            # Validate key
            if not isinstance(key, str):
                result.is_valid = False
                result.validation_messages.append(f"Dict key must be string, got {type(key).__name__}")
                continue

            if len(key) > max_key_length:
                result.is_valid = False
                result.validation_messages.append(f"Dict key too long: {key} ({len(key)} > {max_key_length})")
                continue

            if allowed_keys and key not in allowed_keys:
                result.is_valid = False
                result.validation_messages.append(f"Unexpected dict key: {key}")
                self._log_security_event(
                    ThreatType.XSS, ValidationLevel.WARNING, key,
                    f"Unexpected dictionary key: {key}", source, blocked=False
                )
                continue

            # Validate and sanitize value based on type
            if isinstance(value, str):
                value_result = self.validate_string(value, max_value_length, source=f"{source}.{key}")
                if not value_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"{key}: {msg}" for msg in value_result.validation_messages])
                    result.threats_detected.extend(value_result.threats_detected)
                sanitized_dict[key] = value_result.sanitized_value

            elif isinstance(value, dict):
                dict_result = self.validate_dict(value, allowed_keys, max_key_length, max_value_length, f"{source}.{key}")
                if not dict_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"{key}: {msg}" for msg in dict_result.validation_messages])
                    result.threats_detected.extend(dict_result.threats_detected)
                sanitized_dict[key] = dict_result.sanitized_value

            elif isinstance(value, list):
                list_result = self.validate_list(value, max_value_length, f"{source}.{key}")
                if not list_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"{key}: {msg}" for msg in list_result.validation_messages])
                    result.threats_detected.extend(list_result.threats_detected)
                sanitized_dict[key] = list_result.sanitized_value

            elif isinstance(value, (int, float, bool)):
                sanitized_dict[key] = value

            else:
                result.is_valid = False
                result.validation_messages.append(f"Unsupported value type in dict: {type(value).__name__} for key {key}")

        result.sanitized_value = sanitized_dict
        result.validation_time = (datetime.now() - start_time).total_seconds()

        return result

    def validate_list(self, input_list: List[Any], max_item_length: int = 1000,
                     source: str = "unknown") -> ValidationResult:
        """Validate list input recursively"""
        start_time = datetime.now()

        result = ValidationResult(
            is_valid=True,
            sanitized_value=[],
            original_value=input_list.copy(),
            checksum=self._calculate_checksum(str(input_list))
        )

        if not isinstance(input_list, list):
            result.is_valid = False
            result.validation_messages.append(f"Expected list, got {type(input_list).__name__}")
            return result

        sanitized_list = []

        for i, item in enumerate(input_list):
            if isinstance(item, str):
                item_result = self.validate_string(item, max_item_length, source=f"{source}[{i}]")
                if not item_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"[{i}]: {msg}" for msg in item_result.validation_messages])
                    result.threats_detected.extend(item_result.threats_detected)
                sanitized_list.append(item_result.sanitized_value)

            elif isinstance(item, dict):
                dict_result = self.validate_dict(item, None, 100, max_item_length, f"{source}[{i}]")
                if not dict_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"[{i}]: {msg}" for msg in dict_result.validation_messages])
                    result.threats_detected.extend(dict_result.threats_detected)
                sanitized_list.append(dict_result.sanitized_value)

            elif isinstance(item, list):
                list_result = self.validate_list(item, max_item_length, f"{source}[{i}]")
                if not list_result.is_valid:
                    result.is_valid = False
                    result.validation_messages.extend([f"[{i}]: {msg}" for msg in list_result.validation_messages])
                    result.threats_detected.extend(list_result.threats_detected)
                sanitized_list.append(list_result.sanitized_value)

            elif isinstance(item, (int, float, bool)):
                sanitized_list.append(item)

            else:
                result.is_valid = False
                result.validation_messages.append(f"Unsupported item type in list: {type(item).__name__}")

        result.sanitized_value = sanitized_list
        result.validation_time = (datetime.now() - start_time).total_seconds()

        return result

    def validate_json(self, json_string: str, max_length: int = 10000,
                     source: str = "unknown") -> ValidationResult:
        """Validate JSON input"""
        # First validate as string
        string_result = self.validate_string(json_string, max_length, source=source)
        if not string_result.is_valid:
            return string_result

        # Try to parse JSON
        try:
            parsed_json = json.loads(string_result.sanitized_value)

            # Validate the parsed object
            if isinstance(parsed_json, dict):
                return self.validate_dict(parsed_json, source=source)
            elif isinstance(parsed_json, list):
                return self.validate_list(parsed_json, source=source)
            else:
                return ValidationResult(
                    is_valid=True,
                    sanitized_value=parsed_json,
                    original_value=json_string,
                    checksum=string_result.checksum
                )

        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                original_value=json_string,
                validation_messages=[f"Invalid JSON: {str(e)}"],
                checksum=string_result.checksum
            )

    def _sanitize_html(self, input_string: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        # HTML entity encoding
        sanitized = html.escape(input_string)

        # Additional HTML tag removal
        sanitized = re.sub(r'<[^>]+>', '', sanitized)

        return sanitized

    def _sanitize_special_chars(self, input_string: str) -> str:
        """Sanitize special characters that could be used in injection attacks"""
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')

        # Sanitize control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

        # Sanitize dangerous characters in file paths
        sanitized = sanitized.replace('..', '').replace('//', '/')

        return sanitized

    def _calculate_checksum(self, input_value: str) -> str:
        """Calculate SHA-256 checksum for input"""
        return hashlib.sha256(input_value.encode()).hexdigest()

    def _log_security_event(self, threat_type: ThreatType, severity: ValidationLevel,
                           input_value: str, description: str, source: str, blocked: bool = True):
        """Log security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            threat_type=threat_type,
            severity=severity,
            input_value=input_value,
            description=description,
            source=source,
            blocked=blocked
        )

        self.security_events.append(event)

        # Log to system logger
        log_message = f"🚨 {threat_type.value.upper()} detected from {source}: {description}"
        if severity == ValidationLevel.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ValidationLevel.ERROR:
            self.logger.error(log_message)
        elif severity == ValidationLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        threat_counts = {}
        severity_counts = {}
        source_counts = {}

        for event in self.security_events:
            # Count by threat type
            threat_type = event.threat_type.value
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

            # Count by severity
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count by source
            source = event.source
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_events": len(self.security_events),
            "threat_distribution": threat_counts,
            "severity_distribution": severity_counts,
            "source_distribution": source_counts,
            "blocked_events": sum(1 for event in self.security_events if event.blocked),
            "recent_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "threat_type": event.threat_type.value,
                    "severity": event.severity.value,
                    "source": event.source,
                    "description": event.description,
                    "blocked": event.blocked
                }
                for event in self.security_events[-10:]  # Last 10 events
            ]
        }

    def print_security_report(self):
        """Print formatted security report"""
        report = self.get_security_report()

        print("\n" + "="*60)
        print("🛡️ INPUT VALIDATION SECURITY REPORT")
        print("="*60)
        print(f"📊 Total Security Events: {report['total_events']}")
        print(f"🚫 Blocked Events: {report['blocked_events']}")

        if report['threat_distribution']:
            print("\n🎯 Threat Distribution:")
            for threat, count in report['threat_distribution'].items():
                print(f"   {threat}: {count}")

        if report['severity_distribution']:
            print("\n⚠️ Severity Distribution:")
            for severity, count in report['severity_distribution'].items():
                print(f"   {severity}: {count}")

        if report['source_distribution']:
            print("\n📍 Source Distribution:")
            for source, count in report['source_distribution'].items():
                print(f"   {source}: {count}")

        if report['recent_events']:
            print("\n🕐 Recent Events:")
            for event in report['recent_events']:
                status = "🚫 BLOCKED" if event['blocked'] else "⚠️ DETECTED"
                print(f"   {event['timestamp'][:19]} - {event['threat_type']} ({event['severity']}) - {status}")
                print(f"      Source: {event['source']} - {event['description']}")

        print("="*60)

async def test_input_validation():
    """Test the input validation system"""
    print("🧪 Testing Input Validation and Sanitization System...")

    validator = InputValidator()

    # Test cases
    test_cases = [
        ("Safe input", "Hello, world!", True),
        ("XSS attempt", "<script>alert('xss')</script>", False),
        ("SQL injection", "'; DROP TABLE users; --", False),
        ("Path traversal", "../../../etc/passwd", False),
        ("Command injection", "rm -rf /", False),
        ("Code injection", "<?php system($_GET['cmd']); ?>", False),
        ("JSON with XSS", '{"message": "<script>alert(1)</script>"}', False),
        ("Safe JSON", '{"name": "John", "age": 30}', True),
        ("Long input", "A" * 2000, False),
        ("List with XSS", ["safe", "<script>alert(1)</script>", "safe"], False),
    ]

    print("\n🔍 Running validation tests...")

    for test_name, test_input, expected_valid in test_cases:
        print(f"\n📝 Testing: {test_name}")

        if isinstance(test_input, str):
            if test_input.startswith('{') or test_input.startswith('['):
                result = validator.validate_json(test_input, source="test")
            else:
                result = validator.validate_string(test_input, source="test")
        elif isinstance(test_input, list):
            result = validator.validate_list(test_input, source="test")
        else:
            result = validator.validate_dict(test_input, source="test")

        status = "✅" if result.is_valid == expected_valid else "❌"
        print(f"   {status} Expected: {expected_valid}, Got: {result.is_valid}")

        if result.threats_detected:
            print(f"   🚨 Threats detected: {[t.value for t in result.threats_detected]}")

        if result.validation_messages:
            for msg in result.validation_messages:
                print(f"   📄 Message: {msg}")

    # Print security report
    validator.print_security_report()

    print("\n✅ Input validation system test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_input_validation())