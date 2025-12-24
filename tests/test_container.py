"""
Test DI container
"""

from nwtrack.container import Container, Lifetime


def test_container_register() -> None:
    """Test registering and resolving dependencies in the container."""
    container = Container()

    class ServiceA:
        pass

    class ServiceB:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    container.register(ServiceA, lambda c: ServiceA())
    container.register(ServiceB, lambda c: ServiceB(c.resolve(ServiceA)))

    service_b: ServiceB = container.resolve(ServiceB)
    assert service_b is not None
    assert isinstance(service_b, ServiceB)
    assert isinstance(service_b.service_a, ServiceA)


def test_container_transient() -> None:
    """Test transient lifetime in the container."""
    container = Container()

    class ServiceD:
        pass

    container.register(ServiceD, lambda c: ServiceD(), lifetime=Lifetime.TRANSIENT)
    service_d1: ServiceD = container.resolve(ServiceD)
    service_d2: ServiceD = container.resolve(ServiceD)
    assert service_d1 is not service_d2  # Should be different instances


def test_container_singleton() -> None:
    """Test singleton lifetime in the container."""
    container = Container()

    class ServiceC:
        pass

    container.register(ServiceC, lambda c: ServiceC(), lifetime=Lifetime.SINGLETON)

    service_c1: ServiceC = container.resolve(ServiceC)
    service_c2: ServiceC = container.resolve(ServiceC)

    assert service_c1 is service_c2  # Both should be the same instance
