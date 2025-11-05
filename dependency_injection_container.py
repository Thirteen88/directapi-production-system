#!/usr/bin/env python3
"""
Dependency Injection Container for DirectAPI System
AI Agent Review Implementation: Better Testability

This dependency injection system implements the AI agent recommendation
for better code testability and modularity.

Key Features:
✅ Dependency injection pattern implementation
✅ Service locator pattern
✅ Automatic dependency resolution
✅ Configuration management
✅ Test-friendly mock injection
✅ Lifecycle management (singleton/transient)
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, TypeVar, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

T = TypeVar('T')

class ServiceLifetime(Enum):
    """Service lifetime options"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

@dataclass
class ServiceDescriptor:
    """Descriptor for service registration"""
    interface: Type
    implementation: Type
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    dependencies: List[Type] = field(default_factory=list)

class DIContainer:
    """
    Dependency Injection Container implementing AI agent recommendations

    Benefits:
    ✅ Better testability (core AI recommendation)
    ✅ Loose coupling between components
    ✅ Easy mock injection for testing
    ✅ Configuration-based service management
    ✅ Lifecycle management
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self.logger = logging.getLogger("DIContainer")
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for DI container operations"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register a singleton service"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._services[interface] = descriptor
        self.logger.debug(f"📦 Registered singleton: {interface.__name__} -> {implementation.__name__}")
        return self

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register a transient service (new instance each time)"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT
        )
        self._services[interface] = descriptor
        self.logger.debug(f"📦 Registered transient: {interface.__name__} -> {implementation.__name__}")
        return self

    def register_scoped(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register a scoped service (one instance per scope)"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.SCOPED
        )
        self._services[interface] = descriptor
        self.logger.debug(f"📦 Registered scoped: {interface.__name__} -> {implementation.__name__}")
        return self

    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """Register a specific instance (useful for testing mocks)"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=type(instance),
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance
        )
        self._services[interface] = descriptor
        self._singletons[interface] = instance
        self.logger.debug(f"📦 Registered instance: {interface.__name__} -> {type(instance).__name__}")
        return self

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """Register a factory function for service creation"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=type,
            lifetime=ServiceLifetime.TRANSIENT,
            factory=factory
        )
        self._services[interface] = descriptor
        self.logger.debug(f"📦 Registered factory: {interface.__name__}")
        return self

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
        if interface not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered")

        descriptor = self._services[interface]

        # Handle singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(descriptor)
            return self._singletons[interface]

        # Handle scoped
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if interface not in self._scoped_instances:
                self._scoped_instances[interface] = self._create_instance(descriptor)
            return self._scoped_instances[interface]

        # Handle transient
        return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of a service"""
        if descriptor.instance:
            return descriptor.instance

        if descriptor.factory:
            return descriptor.factory()

        # Get constructor signature and resolve dependencies
        implementation = descriptor.implementation
        constructor_signature = inspect.signature(implementation.__init__)

        kwargs = {}
        for param_name, param in constructor_signature.parameters.items():
            if param_name == 'self':
                continue

            # Check if parameter has type annotation
            if param.annotation != inspect.Parameter.empty:
                dependency_type = param.annotation
                if dependency_type in self._services:
                    kwargs[param_name] = self.resolve(dependency_type)

        try:
            instance = implementation(**kwargs)
            self.logger.debug(f"✅ Created instance: {implementation.__name__}")
            return instance
        except Exception as e:
            self.logger.error(f"❌ Failed to create instance {implementation.__name__}: {str(e)}")
            raise

    def create_scope(self) -> 'DIScope':
        """Create a new scope for scoped services"""
        return DIScope(self)

    def clear_scoped(self):
        """Clear all scoped instances"""
        self._scoped_instances.clear()

    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered services"""
        services_info = {}
        for interface, descriptor in self._services.items():
            services_info[interface.__name__] = {
                "implementation": descriptor.implementation.__name__,
                "lifetime": descriptor.lifetime.value,
                "has_instance": interface in self._singletons,
                "has_factory": descriptor.factory is not None
            }
        return services_info

    def print_diagnostic_info(self):
        """Print diagnostic information about the container"""
        print("\n" + "="*60)
        print("🏭 DEPENDENCY INJECTION CONTAINER DIAGNOSTICS")
        print("="*60)

        services_info = self.get_registered_services()
        for service_name, info in services_info.items():
            lifetime_symbol = {
                ServiceLifetime.SINGLETON: "🔵",
                ServiceLifetime.TRANSIENT: "🟢",
                ServiceLifetime.SCOPED: "🟡"
            }.get(ServiceLifetime(info["lifetime"]), "⚪")

            print(f"{lifetime_symbol} {service_name}")
            print(f"   Implementation: {info['implementation']}")
            print(f"   Lifetime: {info['lifetime']}")
            print(f"   Instance Cached: {'Yes' if info['has_instance'] else 'No'}")
            print(f"   Factory: {'Yes' if info['has_factory'] else 'No'}")
            print()

        print(f"📊 Total Singletons: {len(self._singletons)}")
        print(f"📊 Total Scoped: {len(self._scoped_instances)}")
        print("="*60)

class DIScope:
    """Scope for managing scoped service instances"""

    def __init__(self, container: DIContainer):
        self.container = container
        self.logger = logging.getLogger("DIScope")

    def __enter__(self) -> 'DIScope':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service within this scope"""
        return self.container.resolve(interface)

    def dispose(self):
        """Dispose of this scope and clear scoped instances"""
        self.container.clear_scoped()
        self.logger.debug("🧹 Scope disposed")

# Abstract interfaces for DirectAPI system
class IHttpService(ABC):
    """Abstract interface for HTTP services"""
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        pass

class ICacheService(ABC):
    """Abstract interface for caching services"""
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

class IConfigService(ABC):
    """Abstract interface for configuration services"""
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass

class IMonitoringService(ABC):
    """Abstract interface for monitoring services"""
    @abstractmethod
    def log_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        pass

    @abstractmethod
    def log_event(self, event_name: str, data: Optional[Dict[str, Any]] = None):
        pass

# Example implementations
class EnhancedHttpService(IHttpService):
    """Enhanced HTTP service implementation using the enhanced HTTP client"""

    def __init__(self, config_service: IConfigService, monitoring_service: IMonitoringService):
        from enhanced_http_client import EnhancedHttpClient, HttpClientConfig
        self.config_service = config_service
        self.monitoring_service = monitoring_service

        # Configuration from DI
        self.config = HttpClientConfig(
            pool_size=config_service.get("http.pool_size", 100),
            connect_timeout=config_service.get("http.connect_timeout", 10.0),
            total_timeout=config_service.get("http.total_timeout", 30.0)
        )

        self.client: Optional[EnhancedHttpClient] = None

    async def _get_client(self) -> EnhancedHttpClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = EnhancedHttpClient(self.config)
            await self.client.start_session()
        return self.client

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request with monitoring"""
        start_time = asyncio.get_event_loop().time()
        client = await self._get_client()

        try:
            result = await client.get(url, **kwargs)

            # Log metrics
            duration = asyncio.get_event_loop().time() - start_time
            self.monitoring_service.log_metric("http.get.duration", duration, {"url": url})
            self.monitoring_service.log_metric("http.get.success", 1 if result["success"] else 0)

            return result
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.monitoring_service.log_metric("http.get.duration", duration, {"url": url, "error": str(e)})
            self.monitoring_service.log_metric("http.get.error", 1)
            raise

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request with monitoring"""
        start_time = asyncio.get_event_loop().time()
        client = await self._get_client()

        try:
            result = await client.post(url, **kwargs)

            # Log metrics
            duration = asyncio.get_event_loop().time() - start_time
            self.monitoring_service.log_metric("http.post.duration", duration, {"url": url})
            self.monitoring_service.log_metric("http.post.success", 1 if result["success"] else 0)

            return result
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.monitoring_service.log_metric("http.post.duration", duration, {"url": url, "error": str(e)})
            self.monitoring_service.log_metric("http.post.error", 1)
            raise

class MemoryCacheService(ICacheService):
    """In-memory cache service implementation"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("MemoryCacheService")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            item = self._cache[key]
            if "expires_at" in item and item["expires_at"] < datetime.now():
                del self._cache[key]
                return None
            self.logger.debug(f"🎯 Cache hit: {key}")
            return item["value"]

        self.logger.debug(f"❌ Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        expires_at = None
        if ttl:
            expires_at = datetime.fromtimestamp(datetime.now().timestamp() + ttl)

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        self.logger.debug(f"💾 Cache set: {key}")

    def delete(self, key: str):
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"🗑️ Cache deleted: {key}")

class DictConfigService(IConfigService):
    """Dictionary-based configuration service"""

    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        self._config = initial_config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

class LoggingMonitoringService(IMonitoringService):
    """Logging-based monitoring service"""

    def __init__(self):
        self.logger = logging.getLogger("MonitoringService")

    def log_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Log a metric"""
        tag_str = f" [{', '.join(f'{k}={v}' for k, v in (tags or {}).items())}]" if tags else ""
        self.logger.info(f"📊 Metric: {name} = {value}{tag_str}")

    def log_event(self, event_name: str, data: Optional[Dict[str, Any]] = None):
        """Log an event"""
        data_str = f" - {json.dumps(data)}" if data else ""
        self.logger.info(f"📝 Event: {event_name}{data_str}")

async def test_dependency_injection():
    """Test the dependency injection system"""
    print("🧪 Testing Dependency Injection System...")

    # Create and configure container
    container = DIContainer()

    # Register services
    container.register_singleton(IConfigService, DictConfigService)
    container.register_singleton(ICacheService, MemoryCacheService)
    container.register_singleton(IMonitoringService, LoggingMonitoringService)
    container.register_transient(IHttpService, EnhancedHttpService)

    # Configure the config service
    config_service = container.resolve(IConfigService)
    config_service.set("http.pool_size", 50)
    config_service.set("http.connect_timeout", 5.0)

    # Print diagnostic info
    container.print_diagnostic_info()

    # Test service resolution
    print("\n🔄 Testing service resolution...")

    # Test singleton behavior
    config1 = container.resolve(IConfigService)
    config2 = container.resolve(IConfigService)
    print(f"Config service same instance: {config1 is config2}")

    # Test transient behavior
    http1 = container.resolve(IHttpService)
    http2 = container.resolve(IHttpService)
    print(f"HTTP service different instances: {http1 is not http2}")

    # Test dependency injection
    print(f"HTTP service has config: {hasattr(http1, 'config_service')}")
    print(f"HTTP service has monitoring: {hasattr(http1, 'monitoring_service')}")

    # Test scoped services
    print("\n🔍 Testing scoped services...")
    with container.create_scope() as scope:
        service1 = scope.resolve(IHttpService)
        service2 = scope.resolve(IHttpService)
        print(f"Scoped services same within scope: {service1 is service2}")

    print("✅ Dependency injection system test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_dependency_injection())