syntax on                         " Enable syntax highlighting

" Set netrw listing style:
" 0: tree view, 1: thin tree view, 2: long listing, 3: thin long listing
let g:netrw_liststyle = 3         " Use thin long listing style

" Enable relative and absolute line numbers:
set number                        " Show absolute line number for current line

" Tabs & indentation settings:
set tabstop=2                     " Set tab width to 2 spaces
set shiftwidth=2                  " Set indentation level to 2 spaces
set expandtab                     " Convert tabs to spaces
set autoindent                    " Enable auto-indentation

" Disable line wrapping:
set nowrap                        " Disable line wrapping

" Search settings:
set ignorecase                    " Ignore case in search
set smartcase                     " Enable case-sensitive search if uppercase is used

" Highlight the current cursor line:
set cursorline                    " Highlight the current line

" Enable true color support:
set termguicolors                 " Enable 24-bit RGB colors
set background=dark               " Use dark background for colorschemes
set signcolumn=yes                " Always show the sign column

" Configure backspace behavior:
set backspace=indent,eol,start    " Allow backspace over indent, end-of-line, and insertion start

" Clipboard integration:
set clipboard+=unnamedplus        " Use system clipboard for default register

" Split window settings:
set splitright                    " Open vertical splits to the right
set splitbelow                    " Open horizontal splits below

" Disable swap file creation:
set noswapfile                    " Do not create swap files
