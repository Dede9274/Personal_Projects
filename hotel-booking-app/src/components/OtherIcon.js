import React from 'react';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const OtherIcon = ({name, color = '#475467', size = 28}) => (
  <MaterialCommunityIcons name={name} color={color} size={size} />
);

export default OtherIcon;
