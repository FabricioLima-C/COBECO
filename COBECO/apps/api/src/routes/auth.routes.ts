import { Router } from 'express';
import { AuthController } from '../controllers/auth.controller';
import { validateBody } from '../middleware/validation.middleware';
import {
  signUpSchema,
  loginSchema,
  requestPasswordResetSchema,
  resetPasswordSchema,
} from '../validators/auth.validator';

export function createAuthRoutes(authController: AuthController): Router {
  const router = Router();

  router.post('/sign-up', validateBody(signUpSchema), (req, res, next) =>
    authController.signUp(req, res, next)
  );

  router.post('/login', validateBody(loginSchema), (req, res, next) =>
    authController.login(req, res, next)
  );

  router.post('/refresh', (req, res, next) => authController.refresh(req, res, next));

  router.post('/logout', (req, res, next) => authController.logout(req, res, next));

  router.post('/request-password-reset', validateBody(requestPasswordResetSchema), (req, res, next) =>
    authController.requestPasswordReset(req, res, next)
  );

  router.post('/reset-password', validateBody(resetPasswordSchema), (req, res, next) =>
    authController.resetPassword(req, res, next)
  );

  return router;
}
