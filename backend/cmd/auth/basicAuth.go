package auth

var allowedUsers = []User{
	{
		Username: "admin",
		Password: "admin",
	},
	{
		Username: "noy",
		Password: "theQueen",
	},
	{
		Username: "test",
		Password: "1qaz",
	},
}

type User struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func BasicAuth(user User) bool {
	for _, allowedUser := range allowedUsers {
		if user.Username == allowedUser.Username && user.Password == allowedUser.Password {
			return true
		}
	}
	return false
}
