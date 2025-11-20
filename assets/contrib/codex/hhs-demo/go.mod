module hhs-demo

go 1.22

require (
	github.com/charmbracelet/bubbles v0.18.0
	github.com/charmbracelet/bubbletea v0.25.0
	github.com/charmbracelet/lipgloss v0.10.0
)

replace github.com/charmbracelet/bubbles => ./localdeps/github.com/charmbracelet/bubbles

replace github.com/charmbracelet/bubbletea => ./localdeps/github.com/charmbracelet/bubbletea

replace github.com/charmbracelet/lipgloss => ./localdeps/github.com/charmbracelet/lipgloss
