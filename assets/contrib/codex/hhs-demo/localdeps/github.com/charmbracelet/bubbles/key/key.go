package key

type Binding struct {
        keys []string
        help string
}

type bindingOption func(*Binding)

func WithKeys(keys ...string) bindingOption {
        return func(b *Binding) {
                b.keys = append(b.keys, keys...)
        }
}

func WithHelp(_, _ string) bindingOption {
        return func(_ *Binding) {}
}

func NewBinding(opts ...bindingOption) Binding {
        b := &Binding{}
        for _, opt := range opts {
                opt(b)
        }
        return *b
}

// Matches returns true when the key message string matches any of the binding keys.
func Matches(msg interface{ String() string }, binding Binding) bool {
        msgStr := msg.String()
        for _, k := range binding.keys {
                if k == msgStr {
                        return true
                }
        }
        return false
}
