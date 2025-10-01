
from pyhamilton import HamiltonInterface, INITIALIZE
with HamiltonInterface() as ham_int:
    ham_int.wait_on_response(ham_int.send_command(INITIALIZE), timeout=10)