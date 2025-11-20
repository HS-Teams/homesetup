package help

type Model struct{}

func New() Model {
        return Model{}
}

func (Model) View(_ interface{}) string {
        return ""
}
