import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import Auth from './Auth';
import registerServiceWorker from './registerServiceWorker';

ReactDOM.render(<Auth />, document.getElementById('root'));
registerServiceWorker();
