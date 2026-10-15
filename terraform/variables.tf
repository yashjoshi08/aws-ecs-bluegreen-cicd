variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "ecs-bluegreen"
}

variable "github_repo" {
  description = "GitHub repo in the form owner/name"
  type        = string
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "initial_image_tag" {
  type    = string
  default = "1.0.0"
}