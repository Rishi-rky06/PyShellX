import sys
import os
import subprocess
import shlex
import signal

# Cross-platform readline support
try:
    import readline
except ImportError:
    import pyreadline3 as readline

tab_press_count = 0
last_text = ""

def longest_common_prefix(strings):
    if not strings:
        return ""
    
    prefix = strings[0]
    
    for s in strings[1:]:
        i = 0
        while i < len(prefix) and i < len(s) and prefix[i] == s[i]:
            i += 1
        prefix = prefix[:i]
    
    return prefix

def handle_sigint(signum, frame):
    sys.stdout.write("\n$ ")
    sys.stdout.flush()

def get_path_executables():
    paths = os.environ.get("PATH","").split(os.pathsep)
    executables = set()
    
    for p in paths:
        if not os.path.isdir(p):
            continue
        try:
            for file in os.listdir(p):
                full = os.path.join(p,file)
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    executables.add(file)
        except Exception:
            continue
    return executables

PATH_EXECUTABLES = get_path_executables()

def completer(text, state):
    global tab_press_count, last_text

    buffer = readline.get_line_buffer()
    tokens = buffer.split() 

    # CASE 1: Command completion
    if len(tokens) <= 1 and not buffer.endswith(" "):
        builtins = ['type','echo','exit','pwd','cd','history']
        path_cmds = PATH_EXECUTABLES
        all_cmds = sorted(set(builtins).union(path_cmds))

        matches = [cmd for cmd in all_cmds if cmd.startswith(text)]
        matches.sort()

        if len(matches) == 1:
            return matches[0] + " " if state == 0 else None

        lcp = longest_common_prefix(matches)
        if len(lcp) > len(text):
            return lcp if state == 0 else None

        if text != last_text:
            tab_press_count = 0
            last_text = text

        if tab_press_count == 0 and state == 0:
            tab_press_count += 1
            sys.stdout.write("\x07")
            sys.stdout.flush()

        elif tab_press_count == 1 and state == 0:
            sys.stdout.write("\n")
            sys.stdout.write("  ".join(matches) + "\n")
            sys.stdout.write("$ " + buffer)
            sys.stdout.flush()
            tab_press_count = 0

        return None

   # CASE 2: Filename / Path completion
    else:
        token = text 

        if "/" in token:
            last_slash = token.rfind("/")
            dir_path = token[:last_slash + 1]
            prefix = token[last_slash + 1:]
            search_dir = dir_path if dir_path else "."
        else:
            dir_path = ""
            prefix = token
            search_dir = "."

        try:
            files = os.listdir(search_dir)
        except:
            return None

        matches = [f for f in files if f.startswith(prefix)]
        matches.sort()

        if not matches:
            return None

        if len(matches) == 1:
            match = matches[0]
            full_path = os.path.join(search_dir, match) if search_dir != "." else match
            completion = dir_path + match

            if os.path.isdir(full_path):
                return completion + "/" if state == 0 else None
            else:
                return completion + " " if state == 0 else None

        lcp = longest_common_prefix(matches)
        if len(lcp) > len(prefix):
            return dir_path + lcp if state == 0 else None

        formatted_matches = []
        for m in matches:
            full_path = os.path.join(search_dir, m) if search_dir != "." else m
            if os.path.isdir(full_path):
                formatted_matches.append(m + "/")
            else:
                formatted_matches.append(m)

        if text != last_text:
            tab_press_count = 0
            last_text = text

        if tab_press_count == 0 and state == 0:
            tab_press_count += 1
            sys.stdout.write("\x07")
            sys.stdout.flush()

        elif tab_press_count > 0 and state == 0:
            sys.stdout.write("\n")
            sys.stdout.write("  ".join(formatted_matches) + "\n") 
            sys.stdout.write("$ " + buffer)
            sys.stdout.flush()
            tab_press_count = 0

        return None

def main():
    signal.signal(signal.SIGINT, handle_sigint)
    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
    
    if hasattr(readline, "set_auto_history"):
        readline.set_auto_history(False)
        
    builtins = ['type','echo','exit','pwd','cd','history']
    
    # ---- STARTUP: LOAD HISTORY FROM HISTFILE ----
    histfile = os.environ.get("HISTFILE")
    if histfile and os.path.isfile(histfile):
        try:
            with open(histfile, "r") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.strip():
                        readline.add_history(line)
        except Exception as e:
            sys.stderr.write(f"History load error: {e}\n")

    last_append_index = readline.get_current_history_length()
    
    while True:
        try:
            val = input("$ ")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
        if val.strip():
            # Unconditional add to pass duplicate history tests
            readline.add_history(val)
                
        # ---- MULTI-STAGE PIPELINE WITH BUILTINS ----
        if "|" in val:
            commands = [shlex.split(cmd.strip()) for cmd in val.split("|")]
            
            def run_builtin(cmd_parts, input_data=None):
                cmd = cmd_parts[0]

                if cmd == "echo":
                    return (" ".join(cmd_parts[1:]) + "\n").encode()

                elif cmd == "pwd":
                    return (os.getcwd() + "\n").encode()
                
                elif cmd == "history":
                    # ---- history -r FILE ----
                    if len(cmd_parts) >= 3 and cmd_parts[1] == "-r":
                        file_path = cmd_parts[2]
                        try:
                            with open(file_path, "r") as f:
                                for line in f:
                                    line = line.rstrip("\n")
                                    if line.strip():
                                        readline.add_history(line)
                        except:
                            pass
                        return b""
                        
                    # ---- history -w ----
                    if len(cmd_parts) >= 3 and cmd_parts[1] == "-w":
                        file_path = cmd_parts[2]
                        try:
                            with open(file_path, "w") as f:
                                total = readline.get_current_history_length()
                                for i in range(1, total + 1):
                                    cmd_item = readline.get_history_item(i)
                                    if cmd_item:
                                        f.write(cmd_item + "\n")
                        except:
                            pass
                        return b""
                        
                    # ---- history -a ----
                    if len(cmd_parts) >= 3 and cmd_parts[1] == "-a":
                        file_path = cmd_parts[2]
                        nonlocal last_append_index 
                        try:
                            with open(file_path, "a") as f:
                                total = readline.get_current_history_length()
                                for i in range(last_append_index + 1, total + 1):
                                    cmd_item = readline.get_history_item(i)
                                    if cmd_item:
                                        f.write(cmd_item + "\n")
                                last_append_index = total
                        except:
                            pass
                        return b""

                    # ---- normal history ----
                    n = None
                    if len(cmd_parts) > 1:
                        try:
                            n = int(cmd_parts[1])
                        except:
                            n = None

                    total = readline.get_current_history_length()

                    if n is None or n >= total:
                        start = 1
                    else:
                        start = total - n + 1

                    output = ""
                    for i in range(start, total + 1):
                        cmd_item = readline.get_history_item(i)
                        output += f"    {i}  {cmd_item}\n"

                    return output.encode()

                elif cmd == "type":
                    arg = cmd_parts[1] if len(cmd_parts) > 1 else ""
                    if arg in builtins:
                        return (arg + " is a shell builtin\n").encode()
                    else:
                        paths = os.environ.get("PATH", "").split(os.pathsep)
                        for p in paths:
                            full = os.path.join(p, arg)
                            if os.path.isfile(full) and os.access(full, os.X_OK):
                                return (arg + " is " + full + "\n").encode()
                        return (arg + ": not found\n").encode()

                elif cmd == "cd":
                    try:
                        path = cmd_parts[1] if len(cmd_parts) > 1 else "~"
                        if path == "~":
                            path = os.environ.get("HOME", "")
                        os.chdir(path)
                    except:
                        pass
                    return b""

                return b""

            processes = []
            prev_output = None 

            try:
                for i, cmd_parts in enumerate(commands):
                    is_last = (i == len(commands) - 1)

                    if cmd_parts[0] in builtins:
                        prev_output = run_builtin(cmd_parts, prev_output)
                        if is_last:
                            sys.stdout.write(prev_output.decode())

                    else:
                        if prev_output is not None:
                            p = subprocess.Popen(
                                cmd_parts,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            out, _ = p.communicate(input=prev_output)
                            prev_output = out

                            if is_last:
                                sys.stdout.write(out.decode())

                        else:
                            stdin_source = processes[-1].stdout if processes else None

                            p = subprocess.Popen(
                                cmd_parts,
                                stdin=stdin_source,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )

                            if processes:
                                processes[-1].stdout.close()

                            processes.append(p)

                            if is_last:
                                for line in p.stdout:
                                    sys.stdout.write(line.decode())

                for p in processes:
                    p.wait()

            except FileNotFoundError as e:
                sys.stderr.write(f"{e.filename}: command not found\n")

            continue
        # ---- END PIPELINE ----
        
        new_parts = []
        
        # ---- EXIT: SAVE HISTORY ----
        if val == "exit":
            if histfile:
                try:
                    with open(histfile, "w") as f:
                        total = readline.get_current_history_length()
                        for i in range(1, total + 1):
                            cmd_item = readline.get_history_item(i)
                            if cmd_item:
                                f.write(cmd_item + "\n")
                except Exception as e:
                    sys.stderr.write(f"History save error: {e}\n")
            break
        
        parts = shlex.split(val)
        
        output_file = None
        error_file = None
        append_mode = False
        error_append_mode = False
        
        i=0
        while i < len(parts):
            if parts[i] in [">","1>"]:
                if i+1 < len(parts):
                    output_file = parts[i+1]
                i += 2 
            elif parts[i] in [">>", "1>>"]:
                if i+1 < len(parts):
                    output_file = parts[i+1]
                    append_mode = True
                i+=2
                    
            elif parts[i]=="2>":
                if i+1<len(parts):
                    error_file = parts[i+1]
                i +=2
            elif parts[i] =="2>>":
                if i+1 < len(parts):
                    error_file = parts[i+1]
                    error_append_mode = True
                i+=2
            else:
                new_parts.append(parts[i])
                i +=1
        parts = new_parts
        
        if len(parts) == 0:
            continue
        
        cmd = parts[0]
        
        if cmd=="echo":
            wds = " ".join(parts[1:]) + "\n"
            if output_file:
                mode = "a" if append_mode else "w"
                with open(output_file,mode) as f:
                    f.write(wds)
            else:
                sys.stdout.write(wds)
            
            if error_file:
                mode = "a" if error_append_mode else "w"
                open(error_file,mode).close()
        
        elif cmd=="pwd":
            output = os.getcwd() + "\n"
            if output_file:
                mode = "a" if append_mode else "w"
                with open(output_file,mode) as f:
                    f.write(output)
            else:
                sys.stdout.write(output)
            
            if error_file:
                mode = "a" if error_append_mode else "w"
                open(error_file,mode).close()
        
        elif cmd=="cd":
            path = parts[1] if len(parts) > 1 else "~"
            if path == "~":
                path = os.environ.get("HOME", "")
            
            if os.path.isdir(path):
                os.chdir(path)
            else:
                error_msg = f"cd: {path}: No such file or directory\n" 
                if error_file:
                    mode = "a" if error_append_mode else "w"
                    with open(error_file,mode) as f:
                        f.write(error_msg)
                else : 
                    sys.stderr.write(error_msg) 
        
        elif cmd == "history":
            # ---- history -r FILE ----
            if len(parts) >= 3 and parts[1] == "-r":
                file_path = parts[2]
                try:
                    with open(file_path, "r") as f:
                        for line in f:
                            line = line.rstrip("\n")
                            if line.strip():  
                                readline.add_history(line)
                except:
                    pass
                continue
                
            # ---- history -w FILE ----
            if len(parts) >= 3 and parts[1] == "-w":
                file_path = parts[2]
                try:
                    with open(file_path, "w") as f:
                        total = readline.get_current_history_length()
                        for i in range(1, total + 1):
                            cmd_item = readline.get_history_item(i)
                            if cmd_item:
                                f.write(cmd_item + "\n")
                except:
                    pass
                continue
            
            # ---- history -a FILE ----
            if len(parts) >= 3 and parts[1] == "-a":
                file_path = parts[2]
                try:
                    with open(file_path, "a") as f:
                        total = readline.get_current_history_length()
                        for i in range(last_append_index + 1, total + 1):
                            cmd_item = readline.get_history_item(i)
                            if cmd_item:
                                f.write(cmd_item + "\n")
                        last_append_index = total 
                except:
                    pass
                continue
                
            # ---- normal history printing ----
            n = None
            if len(parts) > 1:
                try:
                    n = int(parts[1])
                except:
                    n = None

            total = readline.get_current_history_length()
            start = 1 if (n is None or n >= total) else (total - n + 1)

            for i in range(start, total + 1):
                cmd_item = readline.get_history_item(i)
                sys.stdout.write(f"    {i}  {cmd_item}\n")
            
        elif cmd=="type":
            arg = "".join(parts[1:])
            if arg in builtins:
                sys.stdout.write(arg+" is a shell builtin\n")
                continue
            else :
                paths = os.environ.get("PATH", "").split(os.pathsep)
                found = False
                for p in paths:
                    full = os.path.join(p,arg)
                    if os.path.isfile(full) and os.access(full,os.X_OK):
                        sys.stdout.write(arg + " is "+ full +"\n")
                        found = True
                        break
                if not found:
                    sys.stdout.write(arg + ": not found\n")                
        else:
           paths = os.environ.get("PATH", "").split(os.pathsep)
           found = False
           
           for p in paths:
               full = os.path.join(p,cmd) 
               if os.path.isfile(full) and os.access(full,os.X_OK):
                   stdout_target = None
                   stderr_target = None
                   if output_file:
                       mode = "a" if append_mode else "w"
                       stdout_target = open(output_file,mode)
                   if error_file:
                       mode = "a" if error_append_mode else "w"
                       stderr_target = open(error_file,mode)
                   
                   subprocess.run([cmd] + parts[1:], executable=full, stdout=stdout_target, stderr=stderr_target)
                   
                   if stdout_target:
                       stdout_target.close()
                   if stderr_target:
                       stderr_target.close()
                   found = True
                   break
               
           if not found:
               error_msg = cmd+": command not found\n"
               if error_file:
                   mode = "a" if error_append_mode else "w"
                   with open(error_file, mode) as f:
                       f.write(error_msg)
               else:
                   sys.stderr.write(error_msg)

if __name__ == "__main__":
    main()
    