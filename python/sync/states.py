import youtrack

fix = "fix"
opn = "open"
rop = "reopen"
inp = "in progress"
dis = "discuss"
crp = "can't reproduce"
obs = "obsolete"
dup = "duplicate"
asd = "as designed"
inv = "invalidate"
wat = "wait"
ver = "verify"
cvr = "can't verify"

advanced_state_machine = {
    "Submitted -> Fixed" : fix,
    "Submitted -> Open" : opn,
    "Submitted -> In Progress" : inp,
    "Submitted -> To be discussed" : dis,
    "Submitted -> Can't Reproduce" : crp,
    "Submitted -> Obsolete" :obs,
    "Submitted -> Duplicate" :dup,
    "Submitted -> As designed" : asd,
    "Submitted -> Invalid" : inv,
    "Open -> In Progress" : inp,
    "Open -> To be discussed" : dis,
    "Open -> Fixed" : fix,
    "Open -> Obsolete" : obs,
    "Open -> Duplicate" : dup,
    "Open -> Can't Reproduce" : crp,
    "Open -> As designed" : asd,
    "Open -> Invalid" : inv,
    "Open -> Wait for Reply" : wat,
    "Reopened -> Open" : opn,
    "Obsolete -> Open" : rop,
    "Duplicate -> Open" : rop,
    "In Progress -> Open" : rop,
    "In Progress -> Fixed" : fix,
    "In Progress -> Can't Reproduce" : crp,
    "In Progress -> Obsolete" : obs,
    "In Progress -> As designed" : asd,
    "To be discussed -> In Progress" : inp,
    "To be discussed -> Duplicate" : dup,
    "To be discussed -> Obsolete" : obs,
    "Can't Reproduce -> Open" : rop,
    "As designed -> Open" : rop,
    "Won't fix -> Open" : rop,
    "Invalid -> Open" : rop,
    "Incomplete -> Open" : rop,
    "Fixed -> Open" : rop,
    "Fixed -> Verified" : ver,
    "Fixed -> W/O verification" : cvr,
    "W/O verification -> Open" : ver,
    "Verified -> Open" : rop,
    "Wait for Reply -> Fixed" : fix,
    "Wait for Reply -> Open" : opn,
    "Wait for Reply -> In Progress" : inp,
    "Wait for Reply -> To be discussed" : dis,
    "Wait for Reply -> Obsolete" : obs,
    "Wait for Reply -> Duplicate" : dup,
    "Wait for Reply -> As designed" :asd,
    "Wait for Reply -> Invalid" : inv
}

def get_event(field):
    old = field.old_value[0] if len(field.old_value) == 1 else None
    new = field.new_value[0] if len(field.new_value) == 1 else None
    if not old or not new : raise ValueError('State can not have multiple value')
    event = advanced_state_machine.get(old + ' -> ' + new)
    if not event: raise LookupError("failed to apply change: State:" + old + "->" + new + " - state machine doesn't allow this transition")
    return event

def get_command_for_state_change(field, with_state_machine):
    return "State " + (get_event(field) if with_state_machine else field.new_value[0]) + " "