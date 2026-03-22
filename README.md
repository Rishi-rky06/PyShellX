# 🐚 PyShellX

A custom Unix-like shell implemented in Python that supports advanced command execution features such as **multi-stage pipelines**, **I/O redirection**, **tab completion**, and **history management**.

This project demonstrates how real shells work internally by recreating core functionalities from scratch using Python.

---

## 🚀 Features

### ✅ Built-in Commands

* `echo` – Print text to output
* `pwd` – Show current directory
* `cd` – Change directory
* `history` – View and manage command history
* `type` – Identify command type (builtin or executable)
* `exit` – Exit the shell

---

### 🔗 Multi-Stage Pipeline Support (Advanced 🚀)

Supports chaining multiple commands together using `|`, including combinations of built-in and external commands.

```bash
echo hello world | tr a-z A-Z | wc
```

✔ Handles:

* Builtin → Builtin
* Builtin → External
* External → External
* Multi-stage pipelines (more than 2 commands)

---

### 📁 I/O Redirection

Supports flexible input/output redirection:

```bash
echo hello > file.txt
echo hello >> file.txt
ls wrong_dir 2> error.txt
```

---

### ⌨️ Smart Tab Completion

* Auto-completes commands and file paths
* Double TAB shows suggestions
* Longest common prefix completion

---

### 🧠 Command History System

* Persistent history via `HISTFILE`
* Commands:

  * `history`
  * `history N`
  * `history -r FILE`
  * `history -w FILE`
  * `history -a FILE`

---

### ⚙️ External Command Execution

* Executes programs from system `$PATH`
* Uses `subprocess` for process control

---

### 🛑 Signal Handling

* Gracefully handles `Ctrl + C` without exiting the shell

---

## 💡 Tricky & Advanced Command Examples

These demonstrate the power of the shell:

### 🔥 Multi-stage pipeline with transformation

```bash
echo one two three | tr a-z A-Z | wc
```

### 🔥 Mixing built-in and external commands

```bash
echo hello world | grep hello
```

### 🔥 Redirection + pipeline

```bash
echo hello world | tr a-z A-Z > output.txt
```

### 🔥 History file manipulation

```bash
history -w myhistory.txt
history -r myhistory.txt
```

### 🔥 Append history incrementally

```bash
history -a myhistory.txt
```

---

## 🛠️ Technologies Used

* Python 3
* `os`
* `sys`
* `subprocess`
* `readline` / `pyreadline3`
* `signal`
* `shlex`

---

## ▶️ How to Run

1. Clone the repository:

```bash
git clone https://github.com/your-username/PyShellX.git
cd PyShellX
```

2. Run the shell:

```bash
python shell.py
```

---

## ⚠️ Notes

* This is a simplified shell, not a full Bash replacement
* Designed for learning systems programming concepts

---

## 📌 Future Improvements

* Environment variable support (`$HOME`, `$PATH`)
* Job control (`fg`, `bg`)
* Shell scripting support
* Better error handling
* Unit testing

---

## 🤝 Contributing

Pull requests are welcome! Feel free to improve or extend the shell.

---
