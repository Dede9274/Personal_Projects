import React from 'react';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const DetailsIcon = ({name, color = '#475467', size = 27}) => (
  <MaterialCommunityIcons name={name} color={color} size={size} />
);

export default DetailsIcon;
