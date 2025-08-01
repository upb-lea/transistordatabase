#!/usr/bin/env python3
"""Test script to verify transistordatabase imports."""


def test_imports():
    """Test importing core classes."""
    try:
        from transistordatabase import Transistor  # noqa: F401
        print('✅ Transistor imported')
    except Exception as e:
        print('❌ Error importing Transistor:', e)

    try:
        from transistordatabase.data_classes import ChannelData  # noqa: F401
        print('✅ ChannelData imported')
    except Exception as e:
        print('❌ Error importing ChannelData:', e)

    try:
        from transistordatabase.switch import Switch  # noqa: F401
        print('✅ Switch imported')
    except Exception as e:
        print('❌ Error importing Switch:', e)

    try:
        from transistordatabase.diode import Diode  # noqa: F401
        print('✅ Diode imported')
    except Exception as e:
        print('❌ Error importing Diode:', e)


if __name__ == "__main__":
    test_imports()
    print("✅ Environment setup completed successfully!")
