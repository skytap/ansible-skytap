Function Get-InstalledPrograms {

    [CmdletBinding(SupportsShouldProcess=$true)]
    param(
        [Parameter(ValueFromPipeline              =$true,
                   ValueFromPipelineByPropertyName=$true,
                   Position=0
        )]
        [string[]]
            $ComputerName = $env:COMPUTERNAME,
        [Parameter(Position=0)]
        [string[]]
            $Property,
        [string[]]
            $IncludeProgram,
        [string[]]
            $ExcludeProgram,
        [switch]
            $ProgramRegExMatch,
        [switch]
            $LastAccessTime,
        [switch]
            $ExcludeSimilar,
        [switch]
            $DisplayRegPath,
        [switch]
            $MicrosoftStore,
        [int]
            $SimilarWord
    )

    begin {
        $RegistryLocation = 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\',
                            'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\'

        if ($psversiontable.psversion.major -gt 2) {
            $HashProperty = [ordered]@{}    
        } else {
            $HashProperty = @{}
            $SelectProperty = @('ComputerName','ProgramName')
            if ($Property) {
                $SelectProperty += $Property
            }
            if ($LastAccessTime) {
                $SelectProperty += 'LastAccessTime'
            }
        }
    }

    process {
		$Computer = $ComputerName[0]
            try {

                    'LocalMachine', 'CurrentUser' | ForEach-Object {
                        $RegName = if ('LocalMachine' -eq $_) {
                            'HKLM:\'
                        } else {
                            'HKCU:\'
                        }

                        if ($MicrosoftStore) {
                            $MSStoreRegPath = 'Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages\'
                            if ('HKCU:\' -eq $RegName) {
                                if ($RegistryLocation -notcontains $MSStoreRegPath) {
                                    $RegistryLocation = $MSStoreRegPath
                                }
                            }
                        }
                        
                        $RegBase = [Microsoft.Win32.RegistryKey]::OpenRemoteBaseKey([Microsoft.Win32.RegistryHive]::$_,$Computer)
                        $RegistryLocation | ForEach-Object {
                            $CurrentReg = $_
                            if ($RegBase) {
                                $CurrentRegKey = $RegBase.OpenSubKey($CurrentReg)
                                if ($CurrentRegKey) {
                                    $CurrentRegKey.GetSubKeyNames() | ForEach-Object {
                                        Write-Verbose -Message ('{0}{1}{2}' -f $RegName, $CurrentReg, $_)

                                        $DisplayName = ($RegBase.OpenSubKey("$CurrentReg$_")).GetValue('DisplayName')
                                        if (($DisplayName -match '^@{.*?}$') -and ($CurrentReg -eq $MSStoreRegPath)) {
                                            $DisplayName = $DisplayName  -replace '.*?\/\/(.*?)\/.*','$1'
                                        }

                                        # $HashProperty.ComputerName = $Computer
 
                                        $HashProperty.ProgramName = $DisplayName
                                        
                                        if ($DisplayRegPath) {
                                            $HashProperty.RegPath = '{0}{1}{2}' -f $RegName, $CurrentReg, $_
                                        } 

                                        if ($IncludeProgram) {
                                            if ($ProgramRegExMatch) {
                                                $IncludeProgram | ForEach-Object {
                                                    if ($DisplayName -notmatch $_) {
                                                        $DisplayName = $null
                                                    }
                                                }
                                            } else {
                                                $IncludeProgram | Where-Object {
                                                    $DisplayName -notlike ($_ -replace '\[','`[')
                                                } | ForEach-Object {
                                                        $DisplayName = $null
                                                }
                                            }
                                        }

                                        if ($ExcludeProgram) {
                                            if ($ProgramRegExMatch) {
                                                $ExcludeProgram | ForEach-Object {
                                                    if ($DisplayName -match $_) {
                                                        $DisplayName = $null
                                                    }
                                                }
                                            } else {
                                                $ExcludeProgram | Where-Object {
                                                    $DisplayName -like ($_ -replace '\[','`[')
                                                } | ForEach-Object {
                                                        $DisplayName = $null
                                                }
                                            }
                                        }

                                        if ($DisplayName) {
                                            if ($Property) {
                                                foreach ($CurrentProperty in $Property) {
                                                    $HashProperty.$CurrentProperty = ($RegBase.OpenSubKey("$CurrentReg$_")).GetValue($CurrentProperty)
                                                }
                                            }
                                            if ($LastAccessTime) {
                                                $InstallPath = ($RegBase.OpenSubKey("$CurrentReg$_")).GetValue('InstallLocation') -replace '\\$',''
                                                if ($InstallPath) {
                                                    $WmiSplat = @{
                                                        ComputerName = $Computer
                                                        Query        = $("ASSOCIATORS OF {Win32_Directory.Name='$InstallPath'} Where ResultClass = CIM_DataFile")
                                                        ErrorAction  = 'SilentlyContinue'
                                                    }
                                                    $HashProperty.LastAccessTime = Get-WmiObject @WmiSplat |
                                                        Where-Object {$_.Extension -eq 'exe' -and $_.LastAccessed} |
                                                        Sort-Object -Property LastAccessed |
                                                        Select-Object -Last 1 | ForEach-Object {
                                                            $_.ConvertToDateTime($_.LastAccessed)
                                                        }
                                                } else {
                                                    $HashProperty.LastAccessTime = $null
                                                }
                                            }

                                            if ($psversiontable.psversion.major -gt 2) {
                                                [pscustomobject]$HashProperty
                                            } else {
                                                New-Object -TypeName PSCustomObject -Property $HashProperty |
                                                Select-Object -Property $SelectProperty
                                            }
                                        }

                                    }

                                }

                            }

                        }
                    }
                }
               catch {
                Write-Error $_
            }
    }
}

$pgms = Get-InstalledPrograms -Property Publisher,InstallDate,DisplayVersion,InstallSource,IsMinorUpgrade,ReleaseType,ParentDisplayName,SystemComponent | Where-Object {[string]$_.SystemComponent -ne 1 -and ![string]$_.IsMinorUpgrade -and ![string]$_.ReleaseType -and ![string]$_.ParentDisplayName} | Sort-Object ProgramName

foreach ($pgm in $pgms) { $pgm | convertTo-json | write-host  }

