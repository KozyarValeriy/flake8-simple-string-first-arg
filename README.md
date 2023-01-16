# flake8-simple-string-first-arg

This *Flake8* plugin for checking that first param of callable object is simple string. 
Plugin will check for specified callable objects that 
it is not allowed to use f-sting, .format method, string concat and % statement for first parameter

# Quick Start Guide

1. Install ``flake8-simple-string-first-arg`` from PyPI with pip:

        pip install flake8-simple-string-first-arg

2. Configure a mark that you would like to validate:

        cd project_root/
        vi setup.cfg

3. Add to file following: 
   
        [flake8]  
        simple-string-first-arg = SomeClassName, OtherClassName:url

3. Run flake8::

        flake8 .

# flake8 codes

   * SFA100: In calling {CallableName} f-string is used
   * SFA200: In calling {CallableName} string.format() is used
   * SFA300: In calling {CallableName} string concatenation ("+") is used
   * SFA400: In calling {CallableName} "%" is used

# Settings

**simple-string-first-arg**  
It specifies a list of name of callable objects, that should have simple string as first arg.
You can add the name of the argument via `:` to check if it is passed as a named parameter.
