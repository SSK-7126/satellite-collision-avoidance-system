import sys
import time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

print("Waiting for Unreal Editor remote execution...")
max_wait = 60
start = time.time()

while time.time() - start < max_wait:
    try:
        remote = remote_execution.RemoteExecution()
        remote.start()
        time.sleep(1.5)
        if remote.remote_nodes:
            print(f"Connected to node: {remote.remote_nodes[0]['node_id']} after {time.time()-start:.1f}s")
            remote.stop()
            sys.exit(0)
        remote.stop()
    except Exception as e:
        pass
    print(f"Loading... ({time.time()-start:.1f}s elapsed)")
    time.sleep(2.0)

print("Timed out waiting for Unreal Editor.")
sys.exit(1)
