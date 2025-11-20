package main

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/help"
	"github.com/charmbracelet/bubbles/key"
tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type topic struct {
	title string
	done  bool
}

type keyMap struct {
	Up     key.Binding
	Down   key.Binding
	Toggle key.Binding
	Reset  key.Binding
	Quit   key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Up, k.Down, k.Toggle, k.Reset, k.Quit}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Toggle, k.Reset},
		{k.Quit},
	}
}

var keys = keyMap{
	Up:     key.NewBinding(key.WithKeys("up", "k"), key.WithHelp("↑/k", "move")),
	Down:   key.NewBinding(key.WithKeys("down", "j"), key.WithHelp("↓/j", "move")),
	Toggle: key.NewBinding(key.WithKeys("enter", " "), key.WithHelp("enter/space", "toggle")),
	Reset:  key.NewBinding(key.WithKeys("r"), key.WithHelp("r", "reset progress")),
	Quit:   key.NewBinding(key.WithKeys("q", "ctrl+c"), key.WithHelp("q", "quit")),
}

type model struct {
	topics []topic
	cursor int
	help   help.Model
	width  int
	height int
}

func newModel() model {
	m := model{
		topics: make([]topic, len(demoTopics)),
		help:   help.New(),
	}

	for i, title := range demoTopics {
		m.topics[i] = topic{title: title}
	}

	return m
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil
	case tea.KeyMsg:
		switch {
		case key.Matches(msg, keys.Up):
			if m.cursor > 0 {
				m.cursor--
			}
		case key.Matches(msg, keys.Down):
			if m.cursor < len(m.topics)-1 {
				m.cursor++
			}
		case key.Matches(msg, keys.Toggle):
			m.topics[m.cursor].done = !m.topics[m.cursor].done
		case key.Matches(msg, keys.Reset):
			for i := range m.topics {
				m.topics[i].done = false
			}
		case key.Matches(msg, keys.Quit):
			return m, tea.Quit
		}
	}

	return m, nil
}

func (m model) View() string {
	header := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("212")).Render("HomeSetup Hands-on Tour")
	subtitle := lipgloss.NewStyle().Foreground(lipgloss.Color("245")).Render("Use the checklist to explore HomeSetup topics. Toggle items as you go.")

	completed := 0
	for _, t := range m.topics {
		if t.done {
			completed++
		}
	}

	progress := lipgloss.NewStyle().Bold(true).Render(fmt.Sprintf("Progress: %d/%d", completed, len(m.topics)))

	listItems := make([]string, len(m.topics))
	for i, t := range m.topics {
		cursor := " "
		if m.cursor == i {
			cursor = "›"
		}

		checkbox := "[ ]"
		titleStyle := lipgloss.NewStyle()
		if t.done {
			checkbox = "[✓]"
			titleStyle = titleStyle.Foreground(lipgloss.Color("120"))
		}

		line := fmt.Sprintf(" %s %s %s", cursor, checkbox, titleStyle.Render(t.title))
		listItems[i] = line
	}

	list := lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("63")).Padding(1).Render(strings.Join(listItems, "\n"))

	detail := lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("244")).Padding(1).Width(48)
	current := m.topics[m.cursor]
	tips := []string{
		"Mark items complete as you finish them.",
		"Use Reset to restart the tour.",
		"Press q to exit when you are done.",
	}

	detailBody := fmt.Sprintf("%s\n\nTopic %d of %d\n\n%s", current.title, m.cursor+1, len(m.topics), strings.Join(tips, "\n"))
	detailBox := detail.Render(detailBody)

	if m.width > 90 {
		content := lipgloss.JoinHorizontal(lipgloss.Top, list, detailBox)
		return lipgloss.JoinVertical(lipgloss.Left, header, subtitle, progress, content, m.help.View(keys))
	}

	return lipgloss.JoinVertical(lipgloss.Left, header, subtitle, progress, list, detailBox, m.help.View(keys))
}

var demoTopics = []string{
	"Introduction to HomeSetup, its purpose, and how it streamlines terminal productivity.",
	"Understanding dotfiles, why they matter, and how HomeSetup manages them safely.",
	"Creating and customizing dotfiles with HomeSetup’s installed templates.",
	"Exploring and setting up aliases tailored to your workflow.",
	"Navigational aliases for quick directory movement and project hopping.",
	"General aliases for common tasks and quality-of-life improvements.",
	"HomeSetup-specific aliases and how they extend standard shell behavior.",
	"Using external tools with HomeSetup (bat, fd, neovim, etc.) and where they hook into the environment.",
	"Terminal shortcuts for efficiency, including prompt controls and cursor helpers.",
	"Key functions provided by HomeSetup and when to apply them.",
	"HHS application overview: plug-ins, functions, and how to list what’s available.",
	"Understanding HHS plug-ins and their purposes.",
	"Exploring HHS functions and how to use them effectively.",
	"Utilizing auto-completions (including Shift+Tab cycling) for faster commands.",
	"Learning how to access and interpret built-in help for functions.",
	"ASK Integration: Using the Ask plug-in to chat with local Ollama models, manage history, and pick models.",
	"FIREBASE Integration: Managing Firebase credentials and settings with HomeSetup’s plug-in.",
	"HSPM Integration: Managing development tools using installation and uninstallation recipes.",
	"SETTINGS Integration: Using the settings manager to modify settings and convert them to .envrc or environment variables.",
	"Starship Setup: Configuring the bundled Starship prompt for a rich, portable shell UI.",
	"ColorLS Integration: Setting up the modern ls replacement and enabling HomeSetup’s aliases for it.",
	"FZF Integration: Using fuzzy finding with key bindings, auto-completions, and bat/fd support.",
	"Ble-sh Integration: Leveraging the Bash line editor with syntax highlighting, auto-suggestions, and Vim modes once installed.",
	"Atuin Integration: Enabling magical shell history with session search and sync-ready defaults after installing Atuin.",
	"Delta Integration: Using Delta as the Git pager with HomeSetup’s default gitconfig snippets for side-by-side diffs.",
	"Zoxide Integration: Faster directory jumps with `z`/`cd`, backed by HomeSetup’s __hhs_change_dir integration.",
	"TLDR Integration: Using `?` or `tldr` for community cheatsheets wired through HomeSetup’s helper.",
	"Ollama / AskAI Integration: Running the Ask plug-in for offline Ollama chat, model management, and automatic service starts.",
}

func main() {
	if err := tea.NewProgram(newModel(), tea.WithAltScreen()).Start(); err != nil {
		fmt.Printf("error: %v\n", err)
	}
}
