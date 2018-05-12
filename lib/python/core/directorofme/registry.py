class RegisterByName:
    '''Generic OAuth client to hold state for all requests'''
    # protocol
    name = None

    @classmethod
    def by_name(cls, name):
        return type(cls).registry.get(name)

    @classmethod
    def make_registrymetaclass(cls):
        class RegistryMeta(type):
            '''Meta class, used to pick which client to use'''
            registry = {}

            def __new__(cls, object_or_name, bases, __dict__):
                built = super().__new__(cls, object_or_name, bases, __dict__)

                name = __dict__.get("name")
                if name is not None:
                    if name in cls.registry:
                        raise TypeError("Class already registered for {} ({})".format(name, built))
                    cls.registry[name] = built

                return built

        return RegistryMeta
