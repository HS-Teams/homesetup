package lipgloss

import "strings"

type Color string

type Border struct{}

type Style struct {
        width int
}

func NewStyle() Style { return Style{} }

func (s Style) Bold(_ bool) Style { return s }

func (s Style) Foreground(_ Color) Style { return s }

func (s Style) Border(_ Border) Style { return s }

func (s Style) BorderForeground(_ Color) Style { return s }

func (s Style) Padding(_ int, _ ...int) Style { return s }

func (s Style) Width(w int) Style { s.width = w; return s }

func (s Style) Render(str string) string { return str }

func RoundedBorder() Border { return Border{} }

func JoinHorizontal(_ Position, strs ...string) string { return strings.Join(strs, " ") }

func JoinVertical(_ Position, strs ...string) string { return strings.Join(strs, "\n") }

type Position int

const (
        Left Position = iota
        Top
)
