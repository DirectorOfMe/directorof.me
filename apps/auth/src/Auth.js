import React, { Component } from 'react';
import './Auth.css';

class Auth extends Component {
  render() {
    return (
      <div className="Auth">
        <h1>Login or Signup</h1>
        <button class="pill">Google</button>
        <button class="pill">Atlassian</button>
        <button class="pill">Github</button>
      </div>
    );
  }
}

export default Auth;
