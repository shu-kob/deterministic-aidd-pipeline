# Sample Requirements: Security Logic Specification

This specification defines the security requirements for our user session module using First-Order Logic (FOL).

- [Req-1] All authenticated users must have an active session:
  forall x (AuthenticatedUser(x) -> HasActiveSession(x))

- [Req-2] A session is active only if it is secure:
  forall y (HasActiveSession(y) -> IsSecureSession(y))
