// ABOUTME: Test fixture — NestJS controller with class and method decorators
// ABOUTME: Exercises the nestjs-routes rule: @Controller prefix + @Get/@Post methods

import { Controller, Get, Post } from "@nestjs/common";

@Controller("users")
export class UsersController {
  @Get()
  findAll() {
    return [];
  }

  @Post("invite")
  invite() {
    return { sent: true };
  }
}
