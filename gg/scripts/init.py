import solve_rec
import os

CnCDir, CNF, numDivides, timeout, timeoutFactor = sys.argv[1:]

marchPath = os.path.join(CnCDir, "march_cu/march_cu")
