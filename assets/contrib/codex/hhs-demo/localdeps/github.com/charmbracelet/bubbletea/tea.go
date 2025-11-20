package bubbletea

import "fmt"

type Msg interface{}

type Cmd func() Msg

type Model interface {
        Init() Cmd
        Update(Msg) (Model, Cmd)
        View() string
}

type Program struct {
        model Model
}

type ProgramOption func(*Program)

type WindowSizeMsg struct {
        Width  int
        Height int
}

type KeyMsg struct {
        Type string
        Rune rune
        Str  string
}

func (k KeyMsg) String() string {
        if k.Str != "" {
                return k.Str
        }
        return k.Type
}

type quitMsg struct{}

var Quit Cmd = func() Msg { return quitMsg{} }

// EnterAltScreen is a no-op command placeholder for compatibility.
func EnterAltScreen() Cmd { return func() Msg { return nil } }

// ExitAltScreen is a no-op command placeholder for compatibility.
func ExitAltScreen() Cmd { return func() Msg { return nil } }

// Sequence runs commands in order and returns the final message.
func Sequence(cmds ...Cmd) Cmd {
        return func() Msg {
                var msg Msg
                for _, cmd := range cmds {
                        if cmd == nil {
                                continue
                        }
                        if res := cmd(); res != nil {
                                msg = res
                        }
                }
                return msg
        }
}

func NewProgram(model Model, _ ...ProgramOption) *Program {
        return &Program{model: model}
}

func (p *Program) Start() error {
        if initCmd := p.model.Init(); initCmd != nil {
                if msg := initCmd(); msg != nil {
                        p.model, _ = p.model.Update(msg)
                }
        }
        fmt.Println(p.model.View())
        return nil
}

func WithAltScreen() ProgramOption { return func(*Program) {} }

func WithMouseCellMotion() ProgramOption { return func(*Program) {} }

func WithInputTTY() ProgramOption { return func(*Program) {} }
